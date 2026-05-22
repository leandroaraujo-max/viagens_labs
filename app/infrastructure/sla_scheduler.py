"""
SLA Scheduler — daemon thread que verifica tokens expirados e cotações atrasadas.

Intervalos:
  - Loop principal: a cada 15 minutos
  - SLA aprovação N1 Comum: 48 h total, lembretes em 24 h e 40 h, aprovação manual em 48 h
  - SLA aprovação N1 Emergencial: 4 h total, lembrete em 2 h, escala N2 em 4 h
  - SLA cotação Comum: 24 h, lembretes em 12 h e 20 h
  - SLA cotação Emergencial: 4 h, lembretes em 2 h e 3.5 h
"""

import logging
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Callable

from sqlalchemy.orm import Session

from app.infrastructure.orm.models import SolicitacaoModel, TokenAprovacaoModel

logger = logging.getLogger(__name__)

# ── Constantes de SLA ─────────────────────────────────────────────────────────
_SLA_APROVACAO_COMUM_H      = 48
_SLA_APROVACAO_EMERG_H      = 4
_LEMBRETE_COMUM_H           = [24, 40]     # Enviar lembrete 1 e 2 antes de expirar
_LEMBRETE_EMERG_H           = [2]          # Só 1 lembrete antes de escalar N2

_SLA_COTACAO_COMUM_H        = 24
_SLA_COTACAO_EMERG_H        = 4
_LEMBRETE_COT_COMUM_H       = [12, 20]
_LEMBRETE_COT_EMERG_H       = [2, 3.5]

_INTERVAL_SEGUNDOS          = 15 * 60       # a cada 15 min


# ── Verificação de tokens de aprovação ───────────────────────────────────────

def _checar_tokens_aprovacao(db: Session) -> None:
    """
    Para cada solicitação AGUARDANDO_N1 ou AGUARDANDO_N2:
    - Envia lembretes conforme SLA
    - Escalona N2 se N1 emergencial expirou
    - Sinaliza aprovação manual se N1 comum expirou 2× sem resposta
    """
    agora = datetime.now(timezone.utc)

    pendentes = (
        db.query(SolicitacaoModel)
        .filter(SolicitacaoModel.status.in_(["AGUARDANDO_N1", "AGUARDANDO_N2"]))
        .all()
    )

    for sol in pendentes:
        token = (
            db.query(TokenAprovacaoModel)
            .filter_by(solicitacao_id=sol.id, status="PENDENTE")
            .order_by(TokenAprovacaoModel.data_criacao.desc())
            .first()
        )
        if not token:
            continue

        # Normaliza timezone
        expira = token.data_expiracao
        if expira.tzinfo is None:
            expira = expira.replace(tzinfo=timezone.utc)

        criado = token.data_criacao
        if criado.tzinfo is None:
            criado = criado.replace(tzinfo=timezone.utc)

        total_h = (expira - criado).total_seconds() / 3600
        passado_h = (agora - criado).total_seconds() / 3600

        is_emergencial = (sol.classificacao == "Emergencial")
        limiares = _LEMBRETE_EMERG_H if is_emergencial else _LEMBRETE_COMUM_H

        # Determina qual lembrete enviar (1-based)
        for idx, limiar_h in enumerate(limiares):
            lembrete_num = idx + 1
            if passado_h >= limiar_h and sol.lembrete_n1_count < lembrete_num:
                try:
                    from app.infrastructure.email_service import EmailService
                    EmailService().enviar_email_lembrete_n1(sol, token, lembrete_num)
                    sol.lembrete_n1_count = lembrete_num
                    db.flush()
                    logger.info(f"[SLA] Lembrete {lembrete_num} enviado → {sol.protocolo}")
                except Exception as e:
                    logger.error(f"[SLA] Falha ao enviar lembrete {lembrete_num} em {sol.protocolo}: {e}")

        # Token expirado?
        if agora >= expira:
            token.status = "EXPIRADO"
            try:
                if is_emergencial and sol.status == "AGUARDANDO_N1":
                    # Escala N2
                    _escalar_n2(db, sol)
                else:
                    # Aprovação manual pelo setor
                    sol.status = "PENDENTE_APROVACAO_MANUAL"
                    from app.infrastructure.email_service import EmailService
                    EmailService().enviar_email_aprovacao_manual(sol)
                    logger.info(f"[SLA] {sol.protocolo} → PENDENTE_APROVACAO_MANUAL")
                db.flush()
            except Exception as e:
                logger.error(f"[SLA] Falha ao processar expiração de {sol.protocolo}: {e}")


def _escalar_n2(db: Session, sol: SolicitacaoModel) -> None:
    """Cria token N2 e notifica quando N1 emergencial expirou."""
    from app.services.aprovacao_service import AprovacaoService
    try:
        svc = AprovacaoService(db)
        token_n2 = svc._criar_token(sol, "N2", sol.aprovador_n2_email, sol.aprovador_n2_nome)
        db.add(token_n2)
        sol.status = "AGUARDANDO_N2"
        db.flush()
        from app.infrastructure.email_service import EmailService
        EmailService().enviar_email_escala_n2(sol, token_n2)
        logger.info(f"[SLA] {sol.protocolo} escalado → N2 ({sol.aprovador_n2_email})")
    except Exception as e:
        logger.error(f"[SLA] Falha ao escalar N2 para {sol.protocolo}: {e}")


# ── Verificação de SLA de cotação ─────────────────────────────────────────────

def _checar_sla_cotacao(db: Session) -> None:
    """
    Para cada solicitação AGUARDANDO_COTACAO:
    - Envia lembretes às agências conforme SLA
    """
    agora = datetime.now(timezone.utc)

    aguardando = (
        db.query(SolicitacaoModel)
        .filter_by(status="AGUARDANDO_COTACAO")
        .all()
    )

    for sol in aguardando:
        criado = sol.data_criacao
        if criado is None:
            continue
        if criado.tzinfo is None:
            criado = criado.replace(tzinfo=timezone.utc)

        passado_h = (agora - criado).total_seconds() / 3600
        is_emergencial = (sol.classificacao == "Emergencial")
        limiares = _LEMBRETE_COT_EMERG_H if is_emergencial else _LEMBRETE_COT_COMUM_H

        for idx, limiar_h in enumerate(limiares):
            lembrete_num = idx + 1
            if passado_h >= limiar_h and sol.lembrete_cot_count < lembrete_num:
                try:
                    from app.infrastructure.email_service import EmailService
                    EmailService().enviar_email_lembrete_cotacao(sol, lembrete_num)
                    sol.lembrete_cot_count = lembrete_num
                    db.flush()
                    logger.info(f"[SLA-Cot] Lembrete {lembrete_num} enviado → {sol.protocolo}")
                except Exception as e:
                    logger.error(f"[SLA-Cot] Falha ao enviar lembrete {lembrete_num} em {sol.protocolo}: {e}")


# ── Loop principal ─────────────────────────────────────────────────────────────

def _loop(session_factory: Callable[[], Session]) -> None:
    logger.info("[SLA Scheduler] Loop iniciado (intervalo: %d s)", _INTERVAL_SEGUNDOS)
    while True:
        try:
            db: Session = session_factory()
            try:
                _checar_tokens_aprovacao(db)
                _checar_sla_cotacao(db)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"[SLA Scheduler] Erro no ciclo: {e}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[SLA Scheduler] Erro crítico ao abrir sessão: {e}")
        time.sleep(_INTERVAL_SEGUNDOS)


def iniciar_scheduler(session_factory: Callable[[], Session]) -> threading.Thread:
    """Inicia o scheduler como daemon thread. Retorna a thread para referência."""
    t = threading.Thread(target=_loop, args=(session_factory,), daemon=True, name="sla-scheduler")
    t.start()
    return t
