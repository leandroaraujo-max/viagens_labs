from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import logging

from app.domain.models import schemas
from app.api.dependencies import get_db_session
from app.infrastructure.ldap_service import ActiveDirectoryService
from app.infrastructure.bigquery_service import BigQueryService
from app.core.security import create_access_token

router = APIRouter()

# Mesma instância do BigQueryService com as tabelas corretas de produção
_bq_service = BigQueryService(
    project_id="maga-bigdata",
    table_assignee="maga-bigdata.kirk.assignee",
    table_funcionarios="maga-bigdata.mlpap.mag_v_funcionarios_ativos",
)


@router.post("/login", response_model=schemas.TokenResponse)
def login(
    credentials: schemas.LoginCredentials,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Valida as credenciais via Active Directory e busca o perfil no BigQuery.
    Retorna JWT + nome de exibição + username AD.
    Agências não usam este endpoint — acesso exclusivo via link/GAS.
    """
    ad_service = ActiveDirectoryService()

    resultado_ad = {"autenticado": False, "perfil": None}
    try:
        resultado_ad = ad_service.autenticar_e_obter_perfil(credentials.username, credentials.password)
    except Exception as e:
        logging.error(f"Falha de comunicação com o AD: {e}")
        # Mesmo se houver erro 500 no AD, gravamos como BLOQUEADO/Erro de Conexão
        try:
            from app.infrastructure.orm.models import LogAcessoModel
            ip_origem = request.client.host if request.client else "127.0.0.1"
            log_acesso = LogAcessoModel(
                username=credentials.username,
                nome="",
                perfil="",
                ip_origem=ip_origem,
                status_acesso="BLOQUEADO",
                observacao=f"Erro de comunicação com o AD: {str(e)}"
            )
            db.add(log_acesso)
            db.commit()
        except Exception as db_err:
            logging.error(f"Erro ao salvar log de erro do AD no banco: {db_err}")
        raise HTTPException(status_code=500, detail="Erro de conexão com servidor de autenticação interna.")

    if not resultado_ad["autenticado"]:
        # Gravar bloqueio no banco de dados antes de levantar exceção
        try:
            from app.infrastructure.orm.models import LogAcessoModel
            ip_origem = request.client.host if request.client else "127.0.0.1"
            obs = "Sem grupo AD elegível para a ferramenta" if resultado_ad.get("sem_grupo") else "Usuário ou senha inválidos no Active Directory"
            log_acesso = LogAcessoModel(
                username=credentials.username,
                nome="",
                perfil="",
                ip_origem=ip_origem,
                status_acesso="BLOQUEADO",
                observacao=obs
            )
            db.add(log_acesso)
            db.commit()
        except Exception as db_err:
            logging.error(f"Erro ao salvar log de bloqueio no banco: {db_err}")

        if resultado_ad.get("sem_grupo"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não possui acesso ao sistema.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos no Active Directory.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Buscar nome real no BigQuery usando o username AD
    colaborador_dados = None
    try:
        colaborador_dados = _bq_service.buscar_colaborador(credentials.username)
    except Exception as e:
        logging.warning(f"Erro ao consultar BQ no login (não crítico): {e}")

    nome_final = colaborador_dados.get("nome") if colaborador_dados else credentials.username
    # perfil vem do grupo AD: "setor" para ADMINS, "dev" para DEV, "viajante" para demais
    perfil_acesso = resultado_ad["perfil"] or "viajante"

    # Gravar sucesso no banco de dados de forma resiliente
    try:
        from app.infrastructure.orm.models import LogAcessoModel
        ip_origem = request.client.host if request.client else "127.0.0.1"
        log_acesso = LogAcessoModel(
            username=credentials.username,
            nome=nome_final,
            perfil=perfil_acesso,
            ip_origem=ip_origem,
            status_acesso="SUCESSO",
            observacao="Login autenticado via AD"
        )
        db.add(log_acesso)
        db.commit()
    except Exception as db_err:
        logging.error(f"Erro ao salvar log de sucesso no banco: {db_err}")

    token_jwt = create_access_token(
        subject=credentials.username,
        perfil=perfil_acesso
    )

    return schemas.TokenResponse(
        access_token=token_jwt,
        nome_usuario=nome_final,
        username=credentials.username,
        perfil=perfil_acesso
    )

