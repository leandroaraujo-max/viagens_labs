from fastapi import APIRouter
from app.api.v1.endpoints import viagens_router, auth_router

api_router = APIRouter()

# Rota para Cria??o de Viagens e Solicita??es
api_router.include_router(viagens_router, prefix="/viagens", tags=["Viagens"])

# Rota para Autentica??o (Login via AD)
api_router.include_router(auth_router, prefix="/auth", tags=["Autentica??o"])
