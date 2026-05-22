from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domain.models import schemas
from app.api.dependencies import get_db_session, get_current_username, get_optional_username
from app.infrastructure.bigquery_service import BigQueryService

router = APIRouter()

bq_service = BigQueryService(
    project_id="maga-bigdata",
    table_assignee="maga-bigdata.kirk.assignee",
    table_funcionarios="maga-bigdata.mlpap.mag_v_funcionarios_ativos",
)


@router.get("/colaborador/{chave_busca}", status_code=200)
def obter_dados_colaborador(
    chave_busca: str,
    _: str | None = Depends(get_optional_username),
):
    """Busca dados de hierarquia no BQ via CPF, Matrícula ou Username do AD."""
    try:
        colaborador = bq_service.buscar_colaborador(chave_busca)
        if not colaborador:
            raise HTTPException(status_code=404, detail="Colaborador inativo ou não encontrado.")
        return {"sucesso": True, "dados": colaborador}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no BQ: {str(e)}")


@router.post("/solicitacoes", response_model=schemas.SolicitacaoResponse, status_code=201)
def criar_solicitacao_de_viagem(
    solicitacao: schemas.SolicitacaoCreate,
    db: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    """Recebe o formulário completo (3 passos) e persiste a solicitação no PostgreSQL."""
    from app.services.viagens_service import ViagensService
    service = ViagensService(db)
    try:
        return service.create_nova_solicitacao(solicitacao, username)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
