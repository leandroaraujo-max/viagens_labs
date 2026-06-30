from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging
from jose import jwt, JWTError

from app.domain.models import schemas
from app.api.dependencies import get_db_session
from app.infrastructure.ldap_service import ActiveDirectoryService
from app.infrastructure.bigquery_service import BigQueryService

# Importamos os itens de segurança necessários
from app.core.security import (
    create_access_token, 
    create_refresh_token, 
    SECRET_KEY, 
    ALGORITHM
)

router = APIRouter()

# Mesma instância do BigQueryService com as tabelas corretas de produção
_bq_service = BigQueryService(
    project_id="maga-bigdata",
    table_assignee="maga-bigdata.kirk.assignee",
    table_funcionarios="maga-bigdata.mlpap.mag_v_funcionarios_ativos",
)

# --- Modelo novo para receber o token na rota de refresh ---
class TokenRefreshRequest(BaseModel):
    refresh_token: str
# -----------------------------------------------------------

@router.post("/login", response_model=schemas.TokenResponse)
@limiter.limit("5/minute")
def login(
    credentials: schemas.LoginCredentials,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Valida as credenciais via Active Directory e busca o perfil no BigQuery.
    Retorna JWT Access, JWT Refresh + nome de exibição + username AD.
    Agências não usam este endpoint — acesso exclusivo via link/GAS.
    """
    ad_service = ActiveDirectoryService()
    resultado_ad = {"autenticado": False, "perfil": None}

    try:
        resultado_ad = ad_service.autenticar_e_obter_perfil(credentials.username, credentials.password)
    except Exception as e:
        logging.error(f"Falha de comunicação com o AD: {e}")
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

    colaborador_dados = None
    try:
        colaborador_dados = _bq_service.buscar_colaborador(credentials.username)
    except Exception as e:
        logging.warning(f"Erro ao consultar BQ no login (não crítico): {e}")

    nome_final = colaborador_dados.get("nome") if colaborador_dados else credentials.username
    perfil_acesso = resultado_ad["perfil"] or "viajante"

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

    # GERAÇÃO DA DUPLA DE TOKENS
    token_jwt = create_access_token(
        subject=credentials.username,
        perfil=perfil_acesso
    )
    
    refresh_jwt = create_refresh_token(
        subject=credentials.username,
        perfil=perfil_acesso
    )

    return schemas.TokenResponse(
        access_token=token_jwt,
        refresh_token=refresh_jwt,
        token_type="bearer",
        nome_usuario=nome_final,
        username=credentials.username,
        perfil=perfil_acesso
    )


@router.post("/refresh")
def refresh_token(request: TokenRefreshRequest):
    """
    Rota silenciosa usada pelo Frontend para manter o usuário logado
    enquanto ele estiver ativo no sistema.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessão expirada por inatividade. Faça login novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Trava de Segurança: impede o uso de um Access Token aqui
        if payload.get("type") != "refresh":
            raise credentials_exception
            
        username: str = payload.get("sub")
        perfil: str = payload.get("perfil")
        
        if not username or not perfil:
            raise credentials_exception
            
    except JWTError:
        # Passou das 4 horas sem uso
        raise credentials_exception

    # O usuário está ativo! Gera tokens novos zerando o cronômetro
    novo_access_token = create_access_token(subject=username, perfil=perfil)
    novo_refresh_token = create_refresh_token(subject=username, perfil=perfil)

    # Não precisamos retornar o schemas.TokenResponse inteiro aqui porque o 
    # frontend já tem o "nome" e "perfil" salvos no LocalStorage desde o login
    return {
        "access_token": novo_access_token,
        "refresh_token": novo_refresh_token,
        "token_type": "bearer"
    }
