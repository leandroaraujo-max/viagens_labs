"""
Endpoints de vouchers.

POST /api/v1/vouchers/{solicitacao_id}/upload
  - Autenticado: agência (require_agencia)
  - Body: multipart/form-data  tipo_voucher + arquivo
  - Responde: { id, solicitacao_id, tipo_voucher, caminho_arquivo, status_solicitacao }
"""

import logging
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.dependencies import get_db_session, require_agencia
from app.infrastructure.orm.models import SolicitacaoModel
from app.services.voucher_service import VoucherService

logger  = logging.getLogger(__name__)
router  = APIRouter(tags=["Vouchers"])
_svc    = VoucherService()

# Limita upload a 20 MB
_MAX_BYTES = 20 * 1024 * 1024


@router.post("/{solicitacao_id}/upload")
async def upload_voucher(
    solicitacao_id: int,
    tipo_voucher:   str         = Form(...),
    arquivo:        UploadFile  = File(...),
    auth:           tuple       = Depends(require_agencia),
    db             = Depends(get_db_session),
):
    """
    Agência faz upload de um voucher para a solicitação aprovada.

    Campos form-data:
    - tipo_voucher: aereo | hospedagem | carro | rodoviario
    - arquivo: PDF, JPG ou PNG (máx 20 MB)
    """
    agencia_usuario, agencia_nome = auth

    sol: SolicitacaoModel = db.query(SolicitacaoModel).filter_by(id=solicitacao_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")

    if sol.status != "APROVADA_AGUARDANDO_VOUCHER":
        raise HTTPException(
            status_code=409,
            detail=f"Voucher não é esperado neste momento (status: {sol.status}).",
        )

    if sol.agencia_vencedora != agencia_nome:
        raise HTTPException(
            status_code=403,
            detail="Apenas a agência vencedora pode enviar vouchers.",
        )

    conteudo = await arquivo.read()
    if len(conteudo) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede 20 MB.")
    if len(conteudo) == 0:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    try:
        voucher = _svc.registrar_voucher(
            db           = db,
            solicitacao  = sol,
            tipo_voucher = tipo_voucher,
            arquivo_bytes= conteudo,
            filename     = arquivo.filename or "voucher.pdf",
        )
        db.commit()
        db.refresh(voucher)
        db.refresh(sol)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        logger.error(f"[Voucher] Erro ao salvar voucher {tipo_voucher} para {sol.protocolo}: {exc}")
        raise HTTPException(status_code=500, detail="Erro interno ao salvar voucher.") from exc

    return {
        "id":                  voucher.id,
        "solicitacao_id":      voucher.solicitacao_id,
        "tipo_voucher":        voucher.tipo_voucher,
        "caminho_arquivo":     voucher.caminho_arquivo,
        "status_solicitacao":  sol.status,
    }
