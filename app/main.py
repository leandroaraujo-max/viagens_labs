import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Configura o root logger para ter timestamps na saída padrão
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("viagenslabs")

# Configuração do Logger de Banco de Dados separado
import os
db_log_dir = r"c:\Projetos\viagens_labs\logs"
if not os.path.exists(db_log_dir):
    db_log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(db_log_dir, exist_ok=True)
db_log_file = os.path.join(db_log_dir, "viagenslabs_db.log")

db_logger = logging.getLogger("sqlalchemy.engine")
db_logger.setLevel(logging.INFO)
db_logger.propagate = False # Evita poluir o viagenslabs_service.out.log principal

# Adiciona o handler de arquivo dedicado ao logger de banco de dados
db_handler = logging.FileHandler(db_log_file, encoding="utf-8")
db_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
db_logger.addHandler(db_handler)

from app.infrastructure.database import Base, engine
from app.infrastructure.orm import models
from app.api.v1.routers import api_router


def _migracoes_seguras():
    """Adiciona colunas novas sem destruir dados existentes (ALTER TABLE IF NOT EXISTS)."""
    from sqlalchemy import text
    sqls = [
        # Fase 1 — colunas originais
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS preferencia_voo TEXT;",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS agencia_vencedora VARCHAR(100);",
        "ALTER TABLE cotacoes DROP CONSTRAINT IF EXISTS cotacoes_solicitacao_id_key;",
        # Fase 5A/5B — contadores SLA
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS lembrete_n1_count  INTEGER DEFAULT 0;",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS lembrete_cot_count INTEGER DEFAULT 0;",
        # Fase 5C — casamentos
        "ALTER TABLE casamentos ADD COLUMN IF NOT EXISTS status        VARCHAR(20) DEFAULT 'PENDENTE';",
        "ALTER TABLE casamentos ADD COLUMN IF NOT EXISTS operador_acao VARCHAR(100) DEFAULT '';",
        "ALTER TABLE casamentos ADD COLUMN IF NOT EXISTS data_acao     TIMESTAMP;",
        "ALTER TABLE casamentos ADD COLUMN IF NOT EXISTS grupo_viagem  VARCHAR(20);",
        # Fase 6 — perfil completo do viajante na solicitação
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS viajante_nome             VARCHAR(200) DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS viajante_cpf              VARCHAR(20)  DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS viajante_matricula        VARCHAR(20)  DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS viajante_email            VARCHAR(200) DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS viajante_cargo            VARCHAR(200) DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS viajante_filial           VARCHAR(20)  DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS viajante_centro_custo     VARCHAR(200) DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS viajante_cod_centro_custo VARCHAR(20)  DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS viajante_data_admissao    VARCHAR(20)  DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS viajante_celular          VARCHAR(20)  DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS viajante_data_nascimento  VARCHAR(20)  DEFAULT '';",
        # Fase 7 — datas independentes do carro + voo de volta
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS carro_data_retirada  VARCHAR(20) DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS carro_data_devolucao VARCHAR(20) DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS preferencia_voo_volta TEXT;",
        # Fase 5A — tokens de acesso por link para agências externas (sem login / sem intranet)
        """CREATE TABLE IF NOT EXISTS tokens_agencia (
            id             SERIAL PRIMARY KEY,
            uuid           VARCHAR(36) UNIQUE NOT NULL,
            solicitacao_id INTEGER REFERENCES solicitacoes(id) NOT NULL,
            agencia_nome   VARCHAR(100) NOT NULL,
            finalidade     VARCHAR(20)  DEFAULT 'COTACAO',
            status         VARCHAR(20)  DEFAULT 'PENDENTE',
            data_expiracao TIMESTAMP    NOT NULL,
            data_criacao   TIMESTAMPTZ  DEFAULT NOW()
        );""",
        "CREATE INDEX IF NOT EXISTS ix_tokens_agencia_uuid ON tokens_agencia(uuid);",
        # Fase 6 — campo de e-mail para usuários de agência
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS email VARCHAR(200) DEFAULT '';",
        # Fase 6B — redesign da tabela de agências (sem login, com CNPJ/endereço/bancário)
        "ALTER TABLE usuarios_agencia DROP COLUMN IF EXISTS username;",
        "ALTER TABLE usuarios_agencia DROP COLUMN IF EXISTS senha_hash;",
        "ALTER TABLE usuarios_agencia DROP COLUMN IF EXISTS nome;",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS razao_social           VARCHAR(200) DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS cnpj                  VARCHAR(20)  DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS inscricao_estadual     VARCHAR(50)  DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS cep                   VARCHAR(10)  DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS logradouro            VARCHAR(200) DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS numero                VARCHAR(20)  DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS complemento           VARCHAR(100) DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS bairro                VARCHAR(100) DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS municipio             VARCHAR(100) DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS uf                    VARCHAR(2)   DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS banco_nome            VARCHAR(100) DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS banco_codigo          VARCHAR(10)  DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS agencia_bancaria      VARCHAR(20)  DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS conta_bancaria        VARCHAR(20)  DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS tipo_conta            VARCHAR(5)   DEFAULT 'CC';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS titularidade_cnpj     VARCHAR(20)  DEFAULT '';",
        "ALTER TABLE usuarios_agencia ADD COLUMN IF NOT EXISTS titularidade_razao_social VARCHAR(200) DEFAULT '';",
        # Fase 6B — datas independentes para hospedagem sem aéreo
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS hosp_data_checkin  VARCHAR(20) DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS hosp_data_checkout VARCHAR(20) DEFAULT '';",
        # Novas Migrações para Cancelamento/Remarcação & Cache Local
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS tipo_solicitacao_cancelamento VARCHAR(50);",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS itens_a_cancelar VARCHAR(200);",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS motivo_cancelamento TEXT DEFAULT '';",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS taxa_cancelamento_agencia NUMERIC;",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS valor_reembolsavel_agencia NUMERIC;",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS valor_credito_gerado NUMERIC;",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS companhia_credito VARCHAR(100);",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS documento_cancelamento_caminho VARCHAR(500);",
        "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS credito_utilizado BOOLEAN DEFAULT FALSE;",
        """CREATE TABLE IF NOT EXISTS colaboradores_cache (
            username          VARCHAR(100) PRIMARY KEY,
            nome              VARCHAR(200) DEFAULT '',
            email             VARCHAR(200) DEFAULT '',
            cargo             VARCHAR(200) DEFAULT '',
            filial            VARCHAR(50)  DEFAULT '',
            centro_custo      VARCHAR(200) DEFAULT '',
            cod_centro_custo  VARCHAR(50)  DEFAULT '',
            data_admissao     VARCHAR(50)  DEFAULT '',
            aprovador_n1_nome VARCHAR(200) DEFAULT '',
            aprovador_n1_email VARCHAR(200) DEFAULT '',
            aprovador_n2_nome VARCHAR(200) DEFAULT '',
            aprovador_n2_email VARCHAR(200) DEFAULT '',
            foneres           VARCHAR(50)  DEFAULT '',
            situacao          VARCHAR(50)  DEFAULT '',
            data_atualizacao  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        "ALTER TABLE colaboradores_cache ADD COLUMN IF NOT EXISTS cpf VARCHAR(20) DEFAULT '';",
        "ALTER TABLE colaboradores_cache ADD COLUMN IF NOT EXISTS matricula VARCHAR(20) DEFAULT '';",
    ]
    with engine.connect() as conn:
        for sql in sqls:
            conn.execute(text(sql))
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Intercepta os logs do Uvicorn para forçar o uso do formato com timestamp
    for name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        l = logging.getLogger(name)
        l.setLevel(logging.INFO)
        for h in l.handlers:
            h.setFormatter(logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            
    logger.info("Conectando ao banco e validando estrutura de tabelas...")
    Base.metadata.create_all(bind=engine)
    _migracoes_seguras()
    logger.info("Estrutura do banco de dados pronta.")
    # Inicia SLA scheduler em thread daemon
    try:
        from app.infrastructure.sla_scheduler import iniciar_scheduler
        from app.infrastructure.database import SessionLocal
        iniciar_scheduler(SessionLocal)
        logger.info("SLA Scheduler iniciado.")
    except Exception as exc:
        logger.warning(f"SLA Scheduler não iniciado: {exc}")
    # Inicia GAS relay scheduler (polling de decisões externas)
    try:
        from app.infrastructure.aprovacao_relay_scheduler import iniciar_relay_scheduler
        from app.infrastructure.database import SessionLocal
        iniciar_relay_scheduler(SessionLocal)
        logger.info("GAS Relay Scheduler iniciado.")
    except Exception as exc:
        logger.warning(f"GAS Relay Scheduler não iniciado: {exc}")
    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title="ViagensLabs API",
        description="Backend baseado em Clean Architecture para gest?o e aprova??o de viagens corporativas.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Configura??o de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware Global de Auditoria de Navegação
    @app.middleware("http")
    async def auditoria_navegacao_middleware(request, call_next):
        path = request.url.path
        if path.startswith("/api/v1/"):
            username = "anônimo"
            perfil = "N/A"
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    token = auth_header.split(" ")[1]
                    from jose import jwt
                    from app.core.security import SECRET_KEY, ALGORITHM
                    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                    username = payload.get("sub", "anônimo")
                    perfil = payload.get("perfil", "N/A")
                except Exception:
                    pass
            logger.info(f"[AUDITORIA - NAVEGAÇÃO] Usuário: {username} | Perfil: {perfil} | Método: {request.method} | Rota: {path}")
        
        response = await call_next(request)
        return response

    # Registra o roteador principal da API
    app.include_router(api_router, prefix="/api/v1")


    # Rota raiz
    @app.get("/")
    def read_root():
        return {
            "message": "Bem-vindo ao ViagensLabs API",
            "documentacao": "/docs",
            "status": "servidor_operacional"
        }

    # Endpoint de saúde aprimorado
    @app.get("/health", tags=["System"])
    def health_check():
        import smtplib
        from app.core.config import settings
        db_ok   = False
        smtp_ok = False
        # Testa DB
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            pass
        # Testa SMTP
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5):
                smtp_ok = True
        except Exception:
            pass
        status = "operacional" if (db_ok and smtp_ok) else "degradado"
        return {"status": status, "db": db_ok, "smtp": smtp_ok}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    from uvicorn.config import LOGGING_CONFIG
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(levelname)s] %(message)s"
    LOGGING_CONFIG["formatters"]["access"]["fmt"] = "%(asctime)s [%(levelname)s] %(client_addr)s - \"%(request_line)s\" %(status_code)s"
    LOGGING_CONFIG["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    LOGGING_CONFIG["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=LOGGING_CONFIG)
