"""
Scheduler que faz polling periódico no GAS Web App relay e processa as decisões
de aprovação N1/N2 feitas por fora da intranet (celular, browser externo).

Inicia uma thread daemon que acorda a cada GAS_POLL_INTERVALO segundos,
verifica se há decisões novas na fila do GAS e processa cada uma via
AprovacaoService.processar_resposta() — o mesmo caminho do portal interno.
"""
import time
import logging
import threading

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Intervalo padrão entre polls (pode ser sobrescrito via GAS_POLL_INTERVALO no .env)
_INTERVALO_PADRAO = 60  # segundos


def _processar_ciclo(SessionLocal) -> None:
    from app.infrastructure.google_relay_service import get_relay
    from app.services.aprovacao_service import AprovacaoService

    relay = get_relay()
    if not relay.disponivel():
        return

    decisoes = relay.poll_decisoes()
    if not decisoes:
        return

    logger.info(f'[GAS relay] {len(decisoes)} decisão(ões) pendente(s).')

    for d in decisoes:
        token_uuid = str(d.get('token', '')).strip()
        decisao    = str(d.get('decisao', '')).strip()
        obs        = str(d.get('observacao', '')).strip()

        if not token_uuid or decisao not in ('APROVADO', 'REPROVADO'):
            logger.warning(f'[GAS relay] Entrada inválida ignorada: {d}')
            if token_uuid:
                relay.marcar_processado(token_uuid)
            continue

        acao = 'aprovar' if decisao == 'APROVADO' else 'reprovar'
        db: Session = SessionLocal()
        try:
            svc = AprovacaoService(db)
            resultado = svc.processar_resposta(token_uuid, acao, obs)

            if resultado is None:
                logger.warning(
                    f'[GAS relay] Token {token_uuid[:8]}… não encontrado no banco '
                    '(já processado internamente ou inválido) — descartando.'
                )
            elif resultado.get('expirado'):
                logger.info(f'[GAS relay] Token {token_uuid[:8]}… expirado — descartando.')
            else:
                logger.info(
                    f'[GAS relay] Protocolo {resultado.get("protocolo")} → '
                    f'{resultado.get("status")} (via GAS, acao={acao})'
                )

            # Marca como processado independente do resultado para evitar loop
            relay.marcar_processado(token_uuid)

        except Exception as exc:
            logger.error(f'[GAS relay] Erro ao processar {token_uuid[:8]}…: {exc}')
        finally:
            db.close()


def _run_loop(SessionLocal, intervalo: int) -> None:
    logger.info(f'[GAS relay] Loop iniciado (intervalo={intervalo}s).')
    while True:
        try:
            _processar_ciclo(SessionLocal)
        except Exception as exc:
            logger.error(f'[GAS relay] Erro no ciclo de poll: {exc}')
        try:
            _processar_ciclo_agencia(SessionLocal)
        except Exception as exc:
            logger.error(f'[GAS relay] Erro no ciclo de poll (agência): {exc}')
        time.sleep(intervalo)


def _processar_ciclo_agencia(SessionLocal) -> None:
    """Processa cotações de agências recebidas via GAS relay."""
    from app.infrastructure.google_relay_service import get_relay
    from app.infrastructure.orm.models import TokenAgenciaModel
    from app.repositories.viagens_repository import ViagensRepository

    relay = get_relay()
    cotacoes = relay.poll_cotacoes()
    if not cotacoes:
        return

    logger.info(f'[GAS relay agência] {len(cotacoes)} cotação(ões) pendente(s).')

    for c in cotacoes:
        token_uuid = str(c.get('token', '')).strip()
        if not token_uuid:
            continue

        db: Session = SessionLocal()
        try:
            repo = ViagensRepository(db)
            tok = db.query(TokenAgenciaModel).filter(
                TokenAgenciaModel.uuid == token_uuid
            ).first()

            if not tok:
                logger.warning(f'[GAS relay agência] Token {token_uuid[:8]}… não encontrado — descartando.')
                relay.marcar_cotacao_processada(token_uuid)
                continue

            if tok.status != 'PENDENTE':
                logger.info(f'[GAS relay agência] Token {token_uuid[:8]}… já processado localmente — sincronizando GAS.')
                relay.marcar_cotacao_processada(token_uuid)
                continue

            from app.domain.models.schemas import CotacaoCreate
            def _flt(val):
                try:
                    return float(val) if val not in (None, '', 'None') else None
                except (ValueError, TypeError):
                    return None

            cotacao_data = CotacaoCreate(
                aereo_companhia       = c.get('aereo_companhia') or None,
                aereo_numero_voo      = c.get('aereo_numero_voo') or None,
                aereo_horario_ida     = c.get('aereo_horario_ida') or None,
                aereo_horario_volta   = c.get('aereo_horario_volta') or None,
                aereo_valor           = _flt(c.get('aereo_valor')),
                hotel_nome            = c.get('hotel_nome') or None,
                hotel_categoria       = c.get('hotel_categoria') or None,
                hotel_valor_diaria    = _flt(c.get('hotel_valor_diaria')),
                rodov_empresa         = c.get('rodov_empresa') or None,
                rodov_horario_ida     = c.get('rodov_horario_ida') or None,
                rodov_horario_volta   = c.get('rodov_horario_volta') or None,
                rodov_valor           = _flt(c.get('rodov_valor')),
                carro_locadora        = c.get('carro_locadora') or None,
                carro_modelo          = c.get('carro_modelo') or None,
                carro_valor_diaria    = _flt(c.get('carro_valor_diaria')),
                valor_total           = _flt(c.get('valor_total')) or 0.0,
                observacoes           = c.get('observacoes') or None,
            )

            from app.services.viagens_service import ViagensService
            svc = ViagensService(db)
            svc.registrar_cotacao_agencia(tok.solicitacao_id, tok.uuid, cotacao_data)

            relay.marcar_cotacao_processada(token_uuid)
            logger.info(f'[GAS relay agência] Cotação {tok.agencia_nome} / {tok.uuid[:8]}… registrada com sucesso.')

        except Exception as exc:
            logger.error(f'[GAS relay agência] Erro ao processar cotação {token_uuid[:8]}…: {exc}')
        finally:
            db.close()


def iniciar_relay_scheduler(SessionLocal) -> None:
    """Inicia a thread daemon de polling do GAS relay."""
    from app.infrastructure.google_relay_service import get_relay
    from app.core.config import settings

    if not get_relay().disponivel():
        logger.info('[GAS relay] GAS_RELAY_URL/GAS_SECRET não configurados — relay desabilitado.')
        return

    intervalo = int(getattr(settings, 'GAS_POLL_INTERVALO', _INTERVALO_PADRAO))
    t = threading.Thread(
        target=_run_loop,
        args=(SessionLocal, intervalo),
        daemon=True,
        name='gas-relay-poll',
    )
    t.start()
    logger.info(f'[GAS relay] Scheduler iniciado (polling a cada {intervalo}s).')
