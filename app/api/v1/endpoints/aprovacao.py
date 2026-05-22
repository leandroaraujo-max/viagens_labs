from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.domain.models.schemas import AprovacaoAcaoRequest
from app.services.aprovacao_service import AprovacaoService

router = APIRouter()


@router.get("/{token_uuid}", summary="Detalhes da solicitação para o portal de aprovação")
def obter_detalhes_aprovacao(token_uuid: str, db: Session = Depends(get_db_session)):
    """
    Retorna os dados da solicitação vinculada ao token.
    Não exige autenticação — o token UUID é o próprio mecanismo de acesso.
    """
    service = AprovacaoService(db)
    detalhes = service.get_detalhes_por_token(token_uuid)
    if not detalhes:
        raise HTTPException(status_code=404, detail="Token inválido.")
    return detalhes


@router.post("/{token_uuid}", summary="Processar aprovação ou reprovação")
def processar_aprovacao(
    token_uuid: str,
    body: AprovacaoAcaoRequest,
    db: Session = Depends(get_db_session),
):
    """
    Registra a decisão do aprovador (aprovar / reprovar).
    Dispara automaticamente o e-mail N2 se a solicitação for Emergencial e N1 aprovou.
    """
    if body.acao not in ("aprovar", "reprovar"):
        raise HTTPException(status_code=400, detail="Ação inválida. Use 'aprovar' ou 'reprovar'.")

    service = AprovacaoService(db)
    resultado = service.processar_resposta(token_uuid, body.acao, body.observacao)

    if resultado is None:
        raise HTTPException(status_code=404, detail="Token inválido ou já utilizado.")
    if resultado.get("expirado"):
        raise HTTPException(
            status_code=410,
            detail="Token expirado. Entre em contato com o setor de viagens.",
        )

    return resultado
