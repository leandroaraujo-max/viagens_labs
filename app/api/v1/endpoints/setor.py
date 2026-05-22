from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.dependencies import get_db_session, require_setor
from app.domain.models.schemas import SolicitacaoSetorResponse, SetorAcaoRequest, CotacaoResponse
from app.services.setor_service import SetorService

router = APIRouter()
_setor_svc = SetorService()

# Campos Optional[str] que devem permanecer None quando o banco retorna NULL
_OPTIONAL_STR_COLS = {'agencia_vencedora'}


def _build_setor_response(sol, cot_tastur, cot_kontrip, casamentos) -> SolicitacaoSetorResponse:
    """Constrói SolicitacaoSetorResponse a partir do ORM e dados relacionados.

    Normaliza None → '' para colunas String/Text e None → False para Boolean,
    exceto campos explicitamente Optional no schema (ex: agencia_vencedora).
    """
    data = {}
    for col in sol.__table__.columns:
        val = getattr(sol, col.name)
        if val is None and col.name not in _OPTIONAL_STR_COLS:
            if isinstance(col.type, (String, Text)):
                val = ''
            elif isinstance(col.type, Boolean):
                val = False
        data[col.name] = val
    data['cotacao_tastur']  = CotacaoResponse.model_validate(cot_tastur)  if cot_tastur  else None
    data['cotacao_kontrip'] = CotacaoResponse.model_validate(cot_kontrip) if cot_kontrip else None
    data['casamentos'] = casamentos
    return SolicitacaoSetorResponse.model_validate(data)


@router.get("/solicitacoes", response_model=List[SolicitacaoSetorResponse])
def listar_solicitacoes(
    status_filtro: Optional[str] = Query(None, description="Filtrar por status"),
    periodo_dias:  Optional[int] = Query(None, description="Últimos N dias"),
    agencia:       Optional[str] = Query(None, description="Filtrar por agência vencedora"),
    busca:         Optional[str] = Query(None, description="Busca livre (protocolo/viajante/destino)"),
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Lista todas as solicitações visíveis no painel do setor, com filtros opcionais."""
    solicitacoes = _setor_svc.listar_solicitacoes(
        db,
        status_filtro=status_filtro,
        periodo_dias=periodo_dias,
        agencia_filtro=agencia,
        busca=busca,
    )
    return [
        _build_setor_response(*_setor_svc.get_solicitacao(db, sol.id))
        for sol in solicitacoes
    ]


@router.get("/solicitacoes/{solicitacao_id}", response_model=SolicitacaoSetorResponse)
def detalhar_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Detalhes completos de uma solicitação para o portal do setor."""
    sol, cot_tastur, cot_kontrip, casamentos = _setor_svc.get_solicitacao(db, solicitacao_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    return _build_setor_response(sol, cot_tastur, cot_kontrip, casamentos)


@router.post("/solicitacoes/{solicitacao_id}/acao", status_code=status.HTTP_200_OK)
def executar_acao(
    solicitacao_id: int,
    body: SetorAcaoRequest,
    db: Session = Depends(get_db_session),
    username: str = Depends(require_setor),
):
    """
    Executa uma ação do setor sobre a solicitação.

    Ações disponíveis por status:
    - PENDENTE_PRE_APROVACAO_SETOR  → PRE_APROVAR | PRE_REPROVAR
    - AGUARDANDO_COTACAO            → REENVIAR_AGENCIAS
    - COTACAO_ENVIADA               → REENVIAR_AGENCIAS
    - PENDENTE_APROVACAO_SETOR_COTACAO → APROVAR_TASTUR | APROVAR_KONTRIP | REPROVAR
    """
    try:
        resultado = _setor_svc.executar_acao(
            db,
            solicitacao_id,
            body.acao,
            body.observacao,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return resultado


# ── Casamentos ────────────────────────────────────────────────────────────────

from app.services.casamento_service import CasamentoService

_casamento_svc = CasamentoService()


@router.get("/casamentos")
def listar_casamentos(
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Lista todos os pares de casamento PENDENTES para o painel do setor."""
    return _casamento_svc.listar_casamentos_pendentes(db)


@router.post("/casamentos/{casamento_id}/vincular")
def vincular_casamento(
    casamento_id: int,
    db: Session = Depends(get_db_session),
    username: str = Depends(require_setor),
):
    """Confirma o match — gera código de grupo e marca como VINCULADO."""
    try:
        casamento = _casamento_svc.vincular(db, casamento_id, username)
        db.commit()
        return {"id": casamento.id, "status": casamento.status, "grupo_viagem": casamento.grupo_viagem}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/casamentos/{casamento_id}/ignorar")
def ignorar_casamento(
    casamento_id: int,
    db: Session = Depends(get_db_session),
    username: str = Depends(require_setor),
):
    """Descarta o match — marca como IGNORADO."""
    try:
        casamento = _casamento_svc.ignorar(db, casamento_id, username)
        db.commit()
        return {"id": casamento.id, "status": casamento.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

