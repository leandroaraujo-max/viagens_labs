"""
LGPD Scheduler — daemon thread que processa solicitações de deleção/anonimização expiradas.

Execução: a cada 1 hora (3600 segundos)
Ação: busca solicitações PENDENTES com data_execucao <= now e executa deleção/anonimização.
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from sqlalchemy.orm import Session

from app.infrastructure.orm.models import (
    LGPDSolicitacaoDelecaoModel,
    SolicitacaoModel,
    TokenAprovacaoModel,
    AuditoriaLGPDModel,
)

logger = logging.getLogger(__name__)

_INTERVAL_SEGUNDOS = 3600  # 1 hora


def _processar_delecoes_expiradas(db: Session) -> None:
    """
    Processa solicitações de deleção LGPD cujo prazo de 30 dias já expirou.
    
    Para cada solicitação:
    - Deleta solicitações de viagem do usuário.
    - Anonimiza tokens de aprovação relacionados.
    - Marca a solicitação de deleção como PROCESSADA.
    - Registra em auditoria LGPD.
    """
    agora = datetime.now(timezone.utc)
    
    expiradas = (
        db.query(LGPDSolicitacaoDelecaoModel)
        .filter(
            LGPDSolicitacaoDelecaoModel.data_execucao <= agora,
            LGPDSolicitacaoDelecaoModel.status == "PENDENTE"
        )
        .all()
    )
    
    if not expiradas:
        return
    
    logger.info(f"[LGPD Scheduler] Processando {len(expiradas)} solicitação(ões) de deleção expirada(s)...")
    
    for solicitacao in expiradas:
        usuario_id = solicitacao.usuario_id
        
        try:
            # 1. Deletar solicitações de viagem do usuário
            solicitacoes_viagem = (
                db.query(SolicitacaoModel)
                .filter(SolicitacaoModel.solicitante_username == usuario_id)
                .all()
            )
            count_viagens = len(solicitacoes_viagem)
            
            for viagem in solicitacoes_viagem:
                db.delete(viagem)
            
            # 2. Anonimizar tokens de aprovação (manter registro de auditoria legal)
            tokens = (
                db.query(TokenAprovacaoModel)
                .filter(TokenAprovacaoModel.email_aprovador.like(f"%{usuario_id}%"))
                .all()
            )
            count_tokens = len(tokens)
            
            for token in tokens:
                token.nome_aprovador = "Anônimo"
                token.email_aprovador = f"DELETED_{uuid4()}"
                token.observacao_resposta = "[LGPD] Dados anonimizados por solicitação do titular"
            
            # 3. Marcar solicitação como processada
            solicitacao.status = "PROCESSADA"
            solicitacao.data_processamento = agora
            solicitacao.observacao = (
                f"Processado automaticamente. "
                f"{count_viagens} viagens deletadas, {count_tokens} tokens anonimizados."
            )
            
            # 4. Registrar em auditoria LGPD
            db.add(
                AuditoriaLGPDModel(
                    usuario_id="SISTEMA_LGPD",
                    acao="DELECAO_AUTOMATICA",
                    recurso=f"usuario:{usuario_id}",
                    dados_acessados=f"{count_viagens} viagens, {count_tokens} tokens",
                    ip_origem="0.0.0.0",
                    user_agent="LGPD Scheduler Daemon",
                )
            )
            
            db.flush()
            
            logger.info(
                f"[LGPD Scheduler] ✓ Usuario {usuario_id} processado: "
                f"{count_viagens} viagens deletadas, {count_tokens} tokens anonimizados."
            )
        
        except Exception as e:
            logger.error(f"[LGPD Scheduler] Erro ao processar usuario {usuario_id}: {e}")
            db.rollback()
            raise


def _loop(session_factory: Callable[[], Session]) -> None:
    """Loop principal do scheduler LGPD."""
    logger.info("[LGPD Scheduler] Loop iniciado (intervalo: %d s)", _INTERVAL_SEGUNDOS)
    while True:
        try:
            db: Session = session_factory()
            try:
                _processar_delecoes_expiradas(db)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"[LGPD Scheduler] Erro no ciclo: {e}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[LGPD Scheduler] Erro crítico no loop: {e}")
        
        time.sleep(_INTERVAL_SEGUNDOS)


def iniciar_lgpd_scheduler(session_factory: Callable[[], Session]) -> None:
    """Inicia o scheduler LGPD em thread daemon."""
    thread = threading.Thread(target=_loop, args=(session_factory,), daemon=True)
    thread.start()
    logger.info("[LGPD Scheduler] Thread daemon iniciado.")
