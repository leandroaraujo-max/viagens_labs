from fastapi import APIRouter
from app.api.v1.endpoints import viagens_router, auth_router, aprovacao_router, agencia_router, duffel_router, setor_router

api_router = APIRouter()

# Criação de solicitações e consulta BQ
api_router.include_router(viagens_router, prefix="/viagens", tags=["Viagens"])

# Autenticação via AD
api_router.include_router(auth_router, prefix="/auth", tags=["Autenticação"])

# Fluxo de aprovação (token-based, sem JWT)
api_router.include_router(aprovacao_router, prefix="/aprovacao", tags=["Aprovação"])

# Portal da agência (Tastur/Kontrip)
api_router.include_router(agencia_router, prefix="/agencia", tags=["Agência"])

# Busca consultiva de voos (Duffel API)
api_router.include_router(duffel_router, prefix="/duffel", tags=["Duffel"])

# Portal do Setor (pré-aprovação e decisão entre cotações)
api_router.include_router(setor_router, prefix="/setor", tags=["Setor"])
