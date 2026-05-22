from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.domain.models import schemas
from app.api.dependencies import get_db_session
from app.infrastructure.bigquery_service import BigQueryService

router = APIRouter()

# Instancia o BQ com as tabelas reais do Luizalabs!
bq_service = BigQueryService(
    project_id="maga-bigdata", 
    table_assignee="maga-bigdata.kirk.assignee", 
    table_funcionarios="maga-bigdata.mlpap.mag_v_funcionarios_ativos"
)

@router.get("/colaborador/{chave_busca}", status_code=200)
def obter_dados_colaborador(chave_busca: str):
    """Busca os dados de hierarquia no BQ via CPF, Matr?cula ou Username."""
    try:
        colaborador = bq_service.buscar_colaborador(chave_busca)
        if not colaborador:
            raise HTTPException(status_code=404, detail="Colaborador inativo ou n?o encontrado.")
        return { "sucesso": True, "dados": colaborador }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no BQ: {str(e)}")

@router.post("/solicitacoes", response_model=schemas.SolicitacaoResponse, status_code=201)
def criar_solicitacao_de_viagem(solicitacao: schemas.SolicitacaoCreate, db: Session = Depends(get_db_session)):
    from app.services.viagens_service import ViagensService
    service = ViagensService(db)
    # TODO: Puxar do JWT
    username_logado = "lnd_araujo"
    try:
        return service.create_nova_solicitacao(solicitacao, username_logado)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
