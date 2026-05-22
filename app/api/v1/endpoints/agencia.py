from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.dependencies import get_db_session, require_agencia
from app.domain.models import schemas
from app.infrastructure.orm.models import CotacaoModel
from app.services.cotacao_service import CotacaoService
from app.services.casamento_service import CasamentoService

router = APIRouter()
_cotacao_svc = CotacaoService()
_casamento_svc = CasamentoService()


@router.get("/solicitacoes", response_model=List[schemas.SolicitacaoAgenciaResponse])
def listar_solicitacoes(
    status_filtro: Optional[str] = None,
    db: Session = Depends(get_db_session),
    agencia_info: tuple = Depends(require_agencia),
):
    """
    Lista as solicitações disponíveis para cotação.
    Filtro opcional: ?status_filtro=AGUARDANDO_COTACAO
    """
    solicitacoes = _cotacao_svc.listar_solicitacoes_agencia(db, status_filtro)
    resultado = []
    for sol in solicitacoes:
        cotacao = db.query(CotacaoModel).filter_by(solicitacao_id=sol.id).first()
        casamentos = _casamento_svc.listar_casamentos_da_solicitacao(db, sol.id)
        resultado.append(
            schemas.SolicitacaoAgenciaResponse(
                id=sol.id,
                protocolo=sol.protocolo,
                solicitante_username=sol.solicitante_username,
                destino_cidade=sol.destino_cidade,
                destino_estado=sol.destino_estado,
                origem_cidade=sol.origem_cidade,
                data_ida=sol.data_ida,
                data_volta=sol.data_volta,
                tipo_servico=sol.tipo_servico,
                classificacao=sol.classificacao,
                status=sol.status,
                motivo_viagem=sol.motivo_viagem,
                aereo_periodo_preferido=sol.aereo_periodo_preferido,
                aereo_tipo_trecho=sol.aereo_tipo_trecho,
                bagagem_extra=sol.bagagem_extra,
                assento_especial=sol.assento_especial,
                rodov_periodo_preferido=sol.rodov_periodo_preferido,
                rodov_tipo_onibus=sol.rodov_tipo_onibus,
                preferencia_hotel_nome=sol.preferencia_hotel_nome,
                carro_cidade_retirada=sol.carro_cidade_retirada,
                carro_hora_retirada=sol.carro_hora_retirada,
                carro_cidade_devolucao=sol.carro_cidade_devolucao,
                carro_hora_devolucao=sol.carro_hora_devolucao,
                observacoes_viajante=sol.observacoes_viajante,
                cotacao=schemas.CotacaoResponse.model_validate(cotacao) if cotacao else None,
                casamentos=casamentos,
            )
        )
    return resultado


@router.get("/solicitacoes/{solicitacao_id}", response_model=schemas.SolicitacaoAgenciaResponse)
def detalhar_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(get_db_session),
    agencia_info: tuple = Depends(require_agencia),
):
    """Detalhes de uma solicitação específica para a agência."""
    sol, cotacao = _cotacao_svc.get_solicitacao_com_cotacao(db, solicitacao_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")

    statuses_visiveis = {"AGUARDANDO_COTACAO", "COTACAO_ENVIADA", "PENDENTE_APROVACAO_SETOR_COTACAO", "APROVADA_AGUARDANDO_VOUCHER", "CONCLUIDA"}
    if sol.status not in statuses_visiveis:
        raise HTTPException(
            status_code=403,
            detail="Solicitação não disponível no portal da agência.",
        )

    casamentos = _casamento_svc.listar_casamentos_da_solicitacao(db, solicitacao_id)
    return schemas.SolicitacaoAgenciaResponse(
        id=sol.id,
        protocolo=sol.protocolo,
        solicitante_username=sol.solicitante_username,
        destino_cidade=sol.destino_cidade,
        destino_estado=sol.destino_estado,
        origem_cidade=sol.origem_cidade,
        data_ida=sol.data_ida,
        data_volta=sol.data_volta,
        tipo_servico=sol.tipo_servico,
        classificacao=sol.classificacao,
        status=sol.status,
        motivo_viagem=sol.motivo_viagem,
        aereo_periodo_preferido=sol.aereo_periodo_preferido,
        aereo_tipo_trecho=sol.aereo_tipo_trecho,
        bagagem_extra=sol.bagagem_extra,
        assento_especial=sol.assento_especial,
        rodov_periodo_preferido=sol.rodov_periodo_preferido,
        rodov_tipo_onibus=sol.rodov_tipo_onibus,
        preferencia_hotel_nome=sol.preferencia_hotel_nome,
        carro_cidade_retirada=sol.carro_cidade_retirada,
        carro_hora_retirada=sol.carro_hora_retirada,
        carro_cidade_devolucao=sol.carro_cidade_devolucao,
        carro_hora_devolucao=sol.carro_hora_devolucao,
        observacoes_viajante=sol.observacoes_viajante,
        cotacao=schemas.CotacaoResponse.model_validate(cotacao) if cotacao else None,
        casamentos=casamentos,
    )


@router.post(
    "/solicitacoes/{solicitacao_id}/cotacao",
    response_model=schemas.CotacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_cotacao(
    solicitacao_id: int,
    dados: schemas.CotacaoCreate,
    db: Session = Depends(get_db_session),
    agencia_info: tuple = Depends(require_agencia),
):
    """Registra ou atualiza a cotação de uma solicitação."""
    agencia_usuario, agencia_nome = agencia_info
    try:
        cotacao = _cotacao_svc.registrar_cotacao(
            db=db,
            solicitacao_id=solicitacao_id,
            dados=dados,
            agencia_usuario=agencia_usuario,
            agencia_nome=agencia_nome,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return schemas.CotacaoResponse.model_validate(cotacao)
