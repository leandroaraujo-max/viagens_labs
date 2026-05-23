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
            raise ValueError("Colaborador inativo ou não encontrado.")
        return {"sucesso": True, "dados": colaborador}
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Falha de conexão BigQuery ({e}). Utilizando fallback mock local.")
        
        nome_sugerido = chave_busca.replace(".", " ").title()
        if len(chave_busca) == 11 and chave_busca.isdigit():
            nome_sugerido = "Sandbox Colaborador CPF"
        elif chave_busca.isdigit() and len(chave_busca) < 10:
            nome_sugerido = "Sandbox Colaborador Matrícula"
            
        mock_data = {
            "nome": nome_sugerido,
            "cpf": "123.456.789-00" if not (chave_busca.isdigit() and len(chave_busca) == 11) else chave_busca,
            "matricula": "CC-1234" if not (chave_busca.isdigit() and len(chave_busca) < 10) else chave_busca,
            "email": f"{chave_busca.lower()}@magazineluiza.com.br" if "@" not in chave_busca else chave_busca,
            "cargo": "Desenvolvedor QA Sênior",
            "filial": "Luizalabs SP",
            "centro_custo": "LUIZALABS - PRODUTO E TECNOLOGIA",
            "cod_centro_custo": "12345",
            "data_admissao": "15/06/2021",
            "aprovador_n1_email": "gestor.sandbox@magazineluiza.com.br",
            "aprovador_n1_nome": "Gestor N1 Sandbox",
            "aprovador_n2_email": "diretoria.sandbox@magazineluiza.com.br",
            "aprovador_n2_nome": "Diretor N2 Sandbox",
        }
        return {"sucesso": True, "dados": mock_data}


@router.get("/perfil/{username}", response_model=schemas.UserProfileData)
def get_perfil_viajante(
    username: str,
    db: Session = Depends(get_db_session),
    _: str | None = Depends(get_optional_username),
):
    """Retorna o perfil salvo do viajante (celular + data nascimento)."""
    from app.infrastructure.orm import models as orm_models
    perfil = db.query(orm_models.UserProfileModel).filter(
        orm_models.UserProfileModel.username == username
    ).first()
    if not perfil:
        return schemas.UserProfileData()
    return perfil


@router.put("/perfil/{username}", response_model=schemas.UserProfileData)
def salvar_perfil_viajante(
    username: str,
    data: schemas.UserProfileData,
    db: Session = Depends(get_db_session),
    _: str | None = Depends(get_optional_username),
):
    """Salva/atualiza o perfil do viajante (upsert)."""
    from app.infrastructure.orm import models as orm_models
    perfil = db.query(orm_models.UserProfileModel).filter(
        orm_models.UserProfileModel.username == username
    ).first()
    if perfil:
        if data.celular:         perfil.celular         = data.celular
        if data.data_nascimento: perfil.data_nascimento = data.data_nascimento
    else:
        perfil = orm_models.UserProfileModel(
            username=username,
            celular=data.celular,
            data_nascimento=data.data_nascimento,
        )
        db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil


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


@router.post("/solicitacoes/{solicitacao_id}/cancelar", status_code=200)
def cancelar_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    """Viajante cancela uma solicitação no status AGUARDANDO_N1 (antes da aprovação)."""
    from app.infrastructure.orm.models import SolicitacaoModel
    sol = db.query(SolicitacaoModel).filter_by(id=solicitacao_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    if sol.solicitante_username != username:
        raise HTTPException(status_code=403, detail="Você não é o solicitante desta viagem.")
    if sol.status != "AGUARDANDO_N1":
        raise HTTPException(
            status_code=409,
            detail=f"Cancelamento não permitido (status atual: {sol.status}). "
                   "Apenas solicitações AGUARDANDO_N1 podem ser canceladas.",
        )
    sol.status = "REPROVADA"
    db.commit()
    return {"protocolo": sol.protocolo, "status": sol.status, "mensagem": "Solicitação cancelada com sucesso."}


@router.get("/minhas", status_code=200)
def listar_minhas_solicitacoes(
    db: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    """Retorna as últimas 20 solicitações do colaborador autenticado."""
    from app.infrastructure.orm.models import SolicitacaoModel
    solicitacoes = (
        db.query(SolicitacaoModel)
        .filter(SolicitacaoModel.solicitante_username == username)
        .order_by(SolicitacaoModel.id.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": s.id,
            "protocolo": s.protocolo,
            "destino_cidade": s.destino_cidade,
            "destino_estado": s.destino_estado,
            "data_ida": s.data_ida,
            "status": s.status.lower() if s.status else "pendente",
            "classificacao": s.classificacao,
            "tipo_servico": s.tipo_servico,
        }
        for s in solicitacoes
    ]
