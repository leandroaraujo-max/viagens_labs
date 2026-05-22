from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Importa as configura??es do banco e do ORM
from app.infrastructure.database import Base, engine
from app.infrastructure.orm import models
# Importa o roteador central que cont?m TODAS as nossas rotas (viagens e auth)
from app.api.v1.routers import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Executado ao iniciar a API: conecta e cria as tabelas"""
    print("Conectando ao banco e validando estrutura de tabelas...")
    Base.metadata.create_all(bind=engine)
    print("Estrutura do banco de dados pronta.")
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

    # Endpoint de sa?de
    @app.get("/health", tags=["System"])
    def health_check():
        return {"status": "operacional"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
