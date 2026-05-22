from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.dependencies import get_db_session, require_setor
from app.domain.models.schemas import SolicitacaoSetorResponse, SetorAcaoRequest
from app.services.setor_service import SetorService

router = APIRouter()
_setor_svc = SetorService()


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
    resultado = []
    for sol in solicitacoes:
        _, cot_tastur, cot_kontrip, casamentos = _setor_svc.get_solicitacao(db, sol.id)
        from app.domain.models.schemas import CotacaoResponse
        resultado.append(
            SolicitacaoSetorResponse(
                id=sol.id,
                protocolo=sol.protocolo,
                solicitante_username=sol.solicitante_username,
                destino_cidade=sol.destino_cidade,
                destino_estado=sol.destino_estado,
                origem_cidade=sol.origem_cidade or "",
                data_ida=sol.data_ida,
                data_volta=sol.data_volta,
                tipo_servico=sol.tipo_servico,
                classificacao=sol.classificacao,
                status=sol.status,
                motivo_viagem=sol.motivo_viagem,
                aereo_periodo_preferido=sol.aereo_periodo_preferido or "",
                aereo_tipo_trecho=sol.aereo_tipo_trecho or "",
                bagagem_extra=sol.bagagem_extra or False,
                assento_especial=sol.assento_especial or "",
                rodov_periodo_preferido=sol.rodov_periodo_preferido or "",
                rodov_tipo_onibus=sol.rodov_tipo_onibus or "",
                preferencia_hotel_nome=sol.preferencia_hotel_nome or "",
                carro_cidade_retirada=sol.carro_cidade_retirada or "",
                carro_hora_retirada=sol.carro_hora_retirada or "",
                carro_cidade_devolucao=sol.carro_cidade_devolucao or "",
                carro_hora_devolucao=sol.carro_hora_devolucao or "",
                observacoes_viajante=sol.observacoes_viajante or "",
                agencia_vencedora=sol.agencia_vencedora,
                cotacao_tastur=CotacaoResponse.model_validate(cot_tastur) if cot_tastur else None,
                cotacao_kontrip=CotacaoResponse.model_validate(cot_kontrip) if cot_kontrip else None,
                casamentos=casamentos,
            )
        )
    return resultado


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

    from app.domain.models.schemas import CotacaoResponse
    return SolicitacaoSetorResponse(
        id=sol.id,
        protocolo=sol.protocolo,
        solicitante_username=sol.solicitante_username,
        destino_cidade=sol.destino_cidade,
        destino_estado=sol.destino_estado,
        origem_cidade=sol.origem_cidade or "",
        data_ida=sol.data_ida,
        data_volta=sol.data_volta,
        tipo_servico=sol.tipo_servico,
        classificacao=sol.classificacao,
        status=sol.status,
        motivo_viagem=sol.motivo_viagem,
        aereo_periodo_preferido=sol.aereo_periodo_preferido or "",
        aereo_tipo_trecho=sol.aereo_tipo_trecho or "",
        bagagem_extra=sol.bagagem_extra or False,
        assento_especial=sol.assento_especial or "",
        rodov_periodo_preferido=sol.rodov_periodo_preferido or "",
        rodov_tipo_onibus=sol.rodov_tipo_onibus or "",
        preferencia_hotel_nome=sol.preferencia_hotel_nome or "",
        carro_cidade_retirada=sol.carro_cidade_retirada or "",
        carro_hora_retirada=sol.carro_hora_retirada or "",
        carro_cidade_devolucao=sol.carro_cidade_devolucao or "",
        carro_hora_devolucao=sol.carro_hora_devolucao or "",
        observacoes_viajante=sol.observacoes_viajante or "",
        agencia_vencedora=sol.agencia_vencedora,
        cotacao_tastur=CotacaoResponse.model_validate(cot_tastur) if cot_tastur else None,
        cotacao_kontrip=CotacaoResponse.model_validate(cot_kontrip) if cot_kontrip else None,
        casamentos=casamentos,
    )


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
