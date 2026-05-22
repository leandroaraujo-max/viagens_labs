from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.domain.models import schemas
from app.api.dependencies import get_db_session
from app.infrastructure.ldap_service import ActiveDirectoryService
from app.infrastructure.bigquery_service import BigQueryService
from app.infrastructure.orm.models import UsuarioAgenciaModel
from app.core.security import create_access_token, verify_password

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
    db: Session = Depends(get_db_session)
):
    """
    Valida as credenciais via Active Directory e busca o perfil no BigQuery.
    Retorna JWT + nome de exibição + username AD.
    """
    if not credentials.agencia:
        ad_service = ActiveDirectoryService()

        resultado_ad = {"autenticado": False, "perfil": None}
        try:
            resultado_ad = ad_service.autenticar_e_obter_perfil(credentials.username, credentials.password)
        except Exception as e:
            logging.error(f"Falha de comunicação com o AD: {e}")
            raise HTTPException(status_code=500, detail="Erro de conexão com servidor de autenticação interna.")

        if not resultado_ad["autenticado"]:
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
        # perfil vem do grupo AD: "setor" para ADMINS, "viajante" para demais
        perfil_acesso = resultado_ad["perfil"] or "viajante"

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

    else:
        # ── Login de agência (Tastur / Kontrip) ───────────────────────────
        usuario = db.query(UsuarioAgenciaModel).filter(
            UsuarioAgenciaModel.username == credentials.username,
            UsuarioAgenciaModel.ativo == True,  # noqa: E712
        ).first()

        if not usuario or not verify_password(credentials.password, usuario.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas para acesso ao portal da agência.",
            )

        token_jwt = create_access_token(
            subject=credentials.username,
            perfil="agencia",
            extra_claims={"agencia_nome": usuario.agencia_nome},
        )
        return schemas.TokenResponse(
            access_token=token_jwt,
            nome_usuario=usuario.nome or credentials.username,
            username=credentials.username,
            perfil="agencia",
        )
