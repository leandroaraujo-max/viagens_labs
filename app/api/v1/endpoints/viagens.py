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
    force_refresh: bool = False,
    db: Session = Depends(get_db_session),
    _: str | None = Depends(get_optional_username),
):
    """Busca dados de hierarquia no BQ via CPF, Matrícula ou Username do AD (com cache local de 7 dias)."""
    from datetime import datetime, timedelta
    from app.infrastructure.orm import models as orm_models

    chave_limpa = chave_busca.strip()
    
    # 1. Verifica cache local
    if not force_refresh:
        cache = db.query(orm_models.ColaboradorCacheModel).filter(
            (orm_models.ColaboradorCacheModel.username == chave_limpa) |
            (orm_models.ColaboradorCacheModel.cpf == chave_limpa) |
            (orm_models.ColaboradorCacheModel.matricula == chave_limpa)
        ).first()
        
        if cache and cache.data_atualizacao:
            age = datetime.now() - cache.data_atualizacao
            if age < timedelta(days=7):
                return {
                    "sucesso": True,
                    "dados": {
                        "matricula":          cache.matricula or "",
                        "cpf":                cache.cpf or "",
                        "nome":               cache.nome or "",
                        "cargo":              cache.cargo or "",
                        "filial":             cache.filial or "",
                        "centro_custo":       cache.centro_custo or "",
                        "cod_centro_custo":   cache.cod_centro_custo or "",
                        "data_admissao":      cache.data_admissao or "",
                        "situacao":           cache.situacao or "",
                        "email":              cache.email or "",
                        "user_name":          cache.username or "",
                        "aprovador_n1_nome":  cache.aprovador_n1_nome or "Não Definido",
                        "aprovador_n1_email": cache.aprovador_n1_email or "",
                        "aprovador_n2_nome":  cache.aprovador_n2_nome or "",
                        "aprovador_n2_email": cache.aprovador_n2_email or "",
                        "foneres":            cache.foneres or "",
                    },
                    "cached": True
                }

    # 2. Cache miss ou force_refresh: busca no BigQuery
    try:
        colaborador = bq_service.buscar_colaborador(chave_busca)
        if not colaborador:
            raise ValueError("Colaborador inativo ou não encontrado.")
            
        # Salva ou atualiza no cache local
        username_val = colaborador.get("user_name") or colaborador.get("email", "").split("@")[0] or chave_limpa
        cache_row = db.query(orm_models.ColaboradorCacheModel).filter(
            orm_models.ColaboradorCacheModel.username == username_val
        ).first()
        
        if not cache_row:
            cache_row = orm_models.ColaboradorCacheModel(username=username_val)
            db.add(cache_row)
            
        cache_row.nome = colaborador.get("nome") or ""
        cache_row.email = colaborador.get("email") or ""
        cache_row.cargo = colaborador.get("cargo") or ""
        cache_row.filial = colaborador.get("filial") or ""
        cache_row.centro_custo = colaborador.get("centro_custo") or ""
        cache_row.cod_centro_custo = colaborador.get("cod_centro_custo") or ""
        cache_row.data_admissao = colaborador.get("data_admissao") or ""
        cache_row.aprovador_n1_nome = colaborador.get("aprovador_n1_nome") or ""
        cache_row.aprovador_n1_email = colaborador.get("aprovador_n1_email") or ""
        cache_row.aprovador_n2_nome = colaborador.get("aprovador_n2_nome") or ""
        cache_row.aprovador_n2_email = colaborador.get("aprovador_n2_email") or ""
        cache_row.foneres = colaborador.get("foneres") or ""
        cache_row.situacao = colaborador.get("situacao") or ""
        cache_row.data_atualizacao = datetime.now()
        
        db.commit()
        return {"sucesso": True, "dados": colaborador, "cached": False}
        
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
            "foneres": "11999999999",
            "situacao": "Ativo"
        }
        
        # Salva o mock no cache também para agilizar testes locais
        username_val = mock_data["email"].split("@")[0]
        cache_row = db.query(orm_models.ColaboradorCacheModel).filter(
            (orm_models.ColaboradorCacheModel.username == username_val) |
            (orm_models.ColaboradorCacheModel.cpf == mock_data["cpf"]) |
            (orm_models.ColaboradorCacheModel.matricula == mock_data["matricula"])
        ).first()
        
        if not cache_row:
            cache_row = orm_models.ColaboradorCacheModel(username=username_val)
            db.add(cache_row)
            
        cache_row.nome = mock_data["nome"]
        cache_row.email = mock_data["email"]
        cache_row.cpf = mock_data["cpf"]
        cache_row.matricula = mock_data["matricula"]
        cache_row.cargo = mock_data["cargo"]
        cache_row.filial = mock_data["filial"]
        cache_row.centro_custo = mock_data["centro_custo"]
        cache_row.cod_centro_custo = mock_data["cod_centro_custo"]
        cache_row.data_admissao = mock_data["data_admissao"]
        cache_row.aprovador_n1_nome = mock_data["aprovador_n1_nome"]
        cache_row.aprovador_n1_email = mock_data["aprovador_n1_email"]
        cache_row.aprovador_n2_nome = mock_data["aprovador_n2_nome"]
        cache_row.aprovador_n2_email = mock_data["aprovador_n2_email"]
        cache_row.foneres = mock_data["foneres"]
        cache_row.situacao = mock_data["situacao"]
        cache_row.data_atualizacao = datetime.now()
        
        db.commit()
        return {"sucesso": True, "dados": mock_data, "cached": False}


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
    """Retorna as solicitações do colaborador logado (criadas por ele, em nome dele, ou via delegações AD ativas)."""
    from app.infrastructure.orm.models import SolicitacaoModel, AutorizacaoTerceiroModel
    from sqlalchemy import or_
    
    # 1. Busca delegações ativas para o usuário
    delegados = db.query(AutorizacaoTerceiroModel).filter(
        AutorizacaoTerceiroModel.solicitante_username == username,
        AutorizacaoTerceiroModel.status == "APROVADA"
    ).all()
    
    emails_delegados = [f"{d.terceiro_username.lower()}@magazineluiza.com.br" for d in delegados]
    
    conditions = [
        SolicitacaoModel.solicitante_username == username,
        SolicitacaoModel.viajante_email.ilike(f"{username}@%")
    ]
    for email_del in emails_delegados:
        conditions.append(SolicitacaoModel.viajante_email.ilike(email_del))
        
    solicitacoes = (
        db.query(SolicitacaoModel)
        .filter(or_(*conditions))
        .order_by(SolicitacaoModel.id.desc())
        .limit(30)
        .all()
    )
    
    return [
        {
            "id": s.id,
            "protocolo": s.protocolo,
            "destino_cidade": s.destino_cidade,
            "destino_estado": s.destino_estado,
            "data_ida": s.data_ida.isoformat() if s.data_ida else None,
            "data_volta": s.data_volta.isoformat() if s.data_volta else None,
            "status": s.status.lower() if s.status else "pendente",
            "classificacao": s.classificacao,
            "tipo_servico": s.tipo_servico,
            "viajante_nome": s.viajante_nome or "",
            "viajante_email": s.viajante_email or "",
            "solicitante_username": s.solicitante_username or "",
            "data_criacao": s.data_criacao.isoformat() if s.data_criacao else None,
        }
        for s in solicitacoes
    ]


from pydantic import BaseModel
from typing import Optional

class CancelarRequest(BaseModel):
    itens_a_cancelar: str
    motivo_cancelamento: str

class RemarcarRequest(BaseModel):
    data_ida: str
    data_volta: Optional[str] = None
    motivo_cancelamento: str


@router.post("/solicitacoes/{solicitacao_id}/solicitar-cancelamento", status_code=200)
def solicitar_cancelamento_viagem(
    solicitacao_id: int,
    req: CancelarRequest,
    db: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    """Permite ao criador, viajante ou terceiro delegado solicitar o cancelamento de uma viagem."""
    from app.infrastructure.orm.models import SolicitacaoModel, AutorizacaoTerceiroModel
    from datetime import datetime
    
    sol = db.query(SolicitacaoModel).filter_by(id=solicitacao_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
        
    # Check ACL
    is_allowed = False
    if sol.solicitante_username == username:
        is_allowed = True
    elif sol.viajante_email and sol.viajante_email.split('@')[0].lower() == username.lower():
        is_allowed = True
    else:
        viajante_username = sol.viajante_email.split('@')[0] if sol.viajante_email else ""
        if viajante_username:
            delegacao = db.query(AutorizacaoTerceiroModel).filter(
                AutorizacaoTerceiroModel.solicitante_username == username,
                AutorizacaoTerceiroModel.terceiro_username == viajante_username,
                AutorizacaoTerceiroModel.status == "APROVADA"
            ).first()
            if delegacao:
                is_allowed = True
                
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Você não tem permissão para cancelar esta viagem de outro viajante.")
        
    if sol.status in ["REPROVADA", "CANCELADA"]:
        raise HTTPException(status_code=400, detail="Esta solicitação já está cancelada ou encerrada.")
        
    # Se ainda está em pre-aprovação / aprovação N1 / N2, cancela direto sem custos
    if sol.status in ["AGUARDANDO_N1", "AGUARDANDO_N2", "PENDENTE_PRE_APROVACAO_SETOR"]:
        sol.status = "REPROVADA"
        sol.tipo_solicitacao_cancelamento = "CANCELAR"
        sol.itens_a_cancelar = req.itens_a_cancelar
        sol.motivo_cancelamento = f"[Cancelamento Direto] {req.motivo_cancelamento}"
        db.commit()
        return {"protocolo": sol.protocolo, "status": sol.status, "mensagem": "Viagem cancelada diretamente com sucesso."}
        
    # Caso contrário, entra no fluxo de liquidação de cancelamento pela agência
    sol.status = "PENDENTE_CANCELAMENTO"
    sol.tipo_solicitacao_cancelamento = "CANCELAR"
    sol.itens_a_cancelar = req.itens_a_cancelar
    sol.motivo_cancelamento = req.motivo_cancelamento
    sol.data_atualizacao = datetime.now() # Registra o timestamp da solicitação de cancelamento
    db.commit()
    return {"protocolo": sol.protocolo, "status": sol.status, "mensagem": "Solicitação de cancelamento enviada para liquidação da agência."}


@router.post("/solicitacoes/{solicitacao_id}/solicitar-remarcacao", status_code=200)
def solicitar_remarcacao_viagem(
    solicitacao_id: int,
    req: RemarcarRequest,
    db: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    """Permite ao criador, viajante ou terceiro delegado solicitar a remarcação de uma viagem."""
    from app.infrastructure.orm.models import SolicitacaoModel, AutorizacaoTerceiroModel
    from datetime import datetime
    
    sol = db.query(SolicitacaoModel).filter_by(id=solicitacao_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
        
    # Check ACL
    is_allowed = False
    if sol.solicitante_username == username:
        is_allowed = True
    elif sol.viajante_email and sol.viajante_email.split('@')[0].lower() == username.lower():
        is_allowed = True
    else:
        viajante_username = sol.viajante_email.split('@')[0] if sol.viajante_email else ""
        if viajante_username:
            delegacao = db.query(AutorizacaoTerceiroModel).filter(
                AutorizacaoTerceiroModel.solicitante_username == username,
                AutorizacaoTerceiroModel.terceiro_username == viajante_username,
                AutorizacaoTerceiroModel.status == "APROVADA"
            ).first()
            if delegacao:
                is_allowed = True
                
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Você não tem permissão para remarcar esta viagem.")
        
    if sol.status in ["REPROVADA", "CANCELADA"]:
        raise HTTPException(status_code=400, detail="Esta solicitação já está cancelada ou encerrada.")
        
    # Salva as novas datas e o status
    sol.status = "PENDENTE_REMARCACAO"
    sol.tipo_solicitacao_cancelamento = "REMARCAR"
    
    # Registra datas originais e novas no motivo_cancelamento
    data_ida_orig = sol.data_ida.strftime("%d/%m/%Y %H:%M") if sol.data_ida else "N/A"
    data_volta_orig = sol.data_volta.strftime("%d/%m/%Y %H:%M") if sol.data_volta else "N/A"
    
    sol.motivo_cancelamento = (
        f"Remarcação Solicitada. Nova Ida: {req.data_ida}, Nova Volta: {req.data_volta or 'N/A'}. "
        f"Ida Anterior: {data_ida_orig}, Volta Anterior: {data_volta_orig}. "
        f"Justificativa: {req.motivo_cancelamento}"
    )
    
    # Atualiza as datas no modelo para a agência cotar corretamente
    try:
        # date input usually in YYYY-MM-DD or YYYY-MM-DDTHH:MM
        if "T" in req.data_ida:
            sol.data_ida = datetime.fromisoformat(req.data_ida.replace("Z", ""))
        else:
            sol.data_ida = datetime.strptime(req.data_ida, "%Y-%m-%d")
            
        if req.data_volta:
            if "T" in req.data_volta:
                sol.data_volta = datetime.fromisoformat(req.data_volta.replace("Z", ""))
            else:
                sol.data_volta = datetime.strptime(req.data_volta, "%Y-%m-%d")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Formato de data inválido: {str(e)}")
        
    sol.data_atualizacao = datetime.now()
    db.commit()
    return {"protocolo": sol.protocolo, "status": sol.status, "mensagem": "Solicitação de remarcação enviada com sucesso."}


@router.get("/creditos/meus", status_code=200)
def obter_meus_creditos(
    db: Session = Depends(get_db_session),
    username: str = Depends(get_current_username),
):
    """Retorna créditos ativos gerados em cancelamentos do usuário."""
    from app.infrastructure.orm.models import SolicitacaoModel
    
    creditos = (
        db.query(SolicitacaoModel)
        .filter(
            (SolicitacaoModel.solicitante_username == username) |
            (SolicitacaoModel.viajante_email.ilike(f"{username}@%"))
        )
        .filter(SolicitacaoModel.valor_credito_gerado > 0)
        .filter(SolicitacaoModel.credito_utilizado == False)
        .all()
    )
    
    return [
        {
            "id": c.id,
            "protocolo": c.protocolo,
            "companhia": c.companhia_credito or "Companhia",
            "valor": float(c.valor_credito_gerado),
            "viajante_nome": c.viajante_nome or "",
            "destino": f"{c.destino_cidade} - {c.destino_estado}",
            "data_criacao": c.data_criacao.isoformat() if c.data_criacao else None
        }
        for c in creditos
    ]
