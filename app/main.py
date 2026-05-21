from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    """
    Factory Pattern para instanciar a aplicação FastAPI.
    Garante inicialização limpa e facilita testes unitários.
    """
    app = FastAPI(
        title="ViagensLabs API",
        description="Backend baseado em Clean Architecture para gestão e aprovação de viagens corporativas.",
        version="1.0.0",
        docs_url="/docs",   # Swagger UI nativo para testes
        redoc_url="/redoc"
    )

    # Diretrizes OWASP: Configuração de CORS (Cross-Origin Resource Sharing)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["System"])
    def health_check():
        """
        Endpoint de liveness para o Windows Server saber que a API está operacional.
        """
        return {"status": "operacional", "ambiente": "Windows Server 2019 (Nativo)", "usuario": "_araujo"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    # Executando passando a instância de "app" diretamente, sem o reload por string
    uvicorn.run(app, host="0.0.0.0", port=8000)

