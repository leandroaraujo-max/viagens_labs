from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.domain.models import schemas
from app.api.dependencies import get_db_session
from app.infrastructure.ldap_service import ActiveDirectoryService
from app.infrastructure.bigquery_service import BigQueryService
from app.core.security import create_access_token

router = APIRouter()

@router.post("/login", response_model=schemas.TokenResponse)
def login(
    credentials: schemas.LoginCredentials,
    db: Session = Depends(get_db_session)
):
    """
    Endpoint central de autentica??o do ViagensLabs.
    Valida as credenciais via Active Directory (LDAP) e busca o perfil no BigQuery.
    Retorna um JWT (JSON Web Token) v?lido.
    """
    if not credentials.agencia:
        # Tenta conectar com o Active Directory
        ad_service = ActiveDirectoryService()
        
        autenticado_ad = False
        try:
            autenticado_ad = ad_service.autenticar_usuario(credentials.username, credentials.password)
        except Exception as e:
            logging.error(f"Falha de comunica??o com o AD: {e}")
            raise HTTPException(status_code=500, detail="Erro de conex?o com servidor de autentica??o interna.")

        if not autenticado_ad:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usu?rio ou senha inv?lidos no Active Directory.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Usu?rio passou no AD. Vamos buscar o nome real dele no BigQuery!
        bq_service = BigQueryService(
            project_id="SEU_PROJECT_ID", 
            table_assignee="SUA_TABELA_ASSIGNEE", 
            table_funcionarios="SUA_TABELA_FUNCIONARIOS"
        )
        
        colaborador_dados = None
        try:
            colaborador_dados = bq_service.buscar_colaborador(credentials.username)
        except Exception as e:
            logging.warning(f"Erro ao consultar o BQ para token. Usando fallback. {e}")

        nome_final = colaborador_dados.get("nome_completo") if colaborador_dados else credentials.username
        perfil_acesso = "viajante"

        token_jwt = create_access_token(
            subject=credentials.username,
            perfil=perfil_acesso
        )

        return schemas.TokenResponse(
            access_token=token_jwt,
            nome_usuario=nome_final,
            perfil=perfil_acesso
        )

    else:
        raise HTTPException(status_code=501, detail="Login de prestador ainda n?o implementado na base PostgreSQL.")
