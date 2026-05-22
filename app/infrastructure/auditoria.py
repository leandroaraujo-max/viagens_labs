"""
Helper de auditoria — grava eventos na tabela log_eventos.

Uso:
    from app.infrastructure.auditoria import log_evento
    log_evento(db, sol.id, "STATUS_CHANGE", de="AGUARDANDO_N1", para="APROVADA", ator=username)
"""

import logging
from sqlalchemy.orm import Session
from app.infrastructure.orm.models import LogEventoModel

logger = logging.getLogger(__name__)


def log_evento(
    db: Session,
    solicitacao_id: int,
    evento: str,
    de_status: str = "",
    para_status: str = "",
    ator: str = "sistema",
    observacao: str = "",
) -> None:
    """Persiste um evento de auditoria. Erros são suprimidos para não bloquear o fluxo principal."""
    try:
        entrada = LogEventoModel(
            solicitacao_id=solicitacao_id,
            evento=evento,
            de_status=de_status,
            para_status=para_status,
            ator=ator,
            observacao=observacao[:2000] if observacao else "",
        )
        db.add(entrada)
        db.flush()
    except Exception as e:
        logger.error(f"[Auditoria] Falha ao gravar log_evento ({evento} / sol_id={solicitacao_id}): {e}")
