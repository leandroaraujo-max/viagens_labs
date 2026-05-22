from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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
    ]
    with engine.connect() as conn:
        for sql in sqls:
            conn.execute(text(sql))
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Conectando ao banco e validando estrutura de tabelas...")
    Base.metadata.create_all(bind=engine)
    _migracoes_seguras()
    print("Estrutura do banco de dados pronta.")
    # Inicia SLA scheduler em thread daemon
    try:
        from app.infrastructure.sla_scheduler import iniciar_scheduler
        from app.infrastructure.database import SessionLocal
        iniciar_scheduler(SessionLocal)
        print("SLA Scheduler iniciado.")
    except Exception as exc:
        print(f"[WARN] SLA Scheduler não iniciado: {exc}")
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
