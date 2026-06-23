from fastapi import APIRouter
from app.api.v1.endpoints import viagens_router, auth_router, aprovacao_router, agencia_router, brasil_api_router, setor_router, voucher_router, dev_router
from app.api.v1.endpoints.terceiros import router as terceiros_router
from app.api.v1.endpoints.hoteis import router as hoteis_router
from app.api.v1.endpoints.lgpd import router as lgpd_router

api_router = APIRouter()

# Criação de solicitações e consulta BQ
api_router.include_router(viagens_router, prefix="/viagens", tags=["Viagens"])

# Autenticação via AD
api_router.include_router(auth_router, prefix="/auth", tags=["Autenticação"])

# Fluxo de aprovação (token-based, sem JWT)
api_router.include_router(aprovacao_router, prefix="/aprovacao", tags=["Aprovação"])

# Portal da agência (Tastur/Kontrip)
api_router.include_router(agencia_router, prefix="/agencia", tags=["Agência"])

# Integração Brasil API (clima de aeroportos e autocomplementação)
api_router.include_router(brasil_api_router, prefix="/brasil-api", tags=["Brasil API"])

# Portal do Setor (pré-aprovação e decisão entre cotações)
api_router.include_router(setor_router, prefix="/setor", tags=["Setor"])

# Upload de vouchers pela agência vencedora
api_router.include_router(voucher_router, prefix="/vouchers", tags=["Vouchers"])

# Portal do Desenvolvedor (G_ACCESS_VIAGENSLABS_DEV — acesso irrestrito)
api_router.include_router(dev_router, prefix="/dev", tags=["Dev"])

# Fluxo de Solicitação para Terceiros (antiga Delegação)
api_router.include_router(terceiros_router, prefix="", tags=["Terceiros"])

# Fluxo de Solicitação para Hotéis
api_router.include_router(hoteis_router, prefix="/hoteis", tags=["Hoteis"])

# LGPD — Consentimento, acesso a dados, direito ao esquecimento
api_router.include_router(lgpd_router, tags=["LGPD"])
