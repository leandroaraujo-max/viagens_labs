from fastapi import APIRouter, HTTPException, Query
import logging

from app.infrastructure.brasil_api_service import BrasilApiService

router = APIRouter()
logger = logging.getLogger(__name__)


def _svc() -> BrasilApiService:
    try:
        return BrasilApiService()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/lugares")
def buscar_lugares(q: str = Query(..., min_length=2, description="Nome de cidade ou aeroporto")):
    """
    Autocomplete de aeroportos e cidades com validação via Brasil API.
    Retorna até 8 sugestões com código IATA.
    """
    try:
        lugares = _svc().buscar_lugares(q)
        return {"sucesso": True, "locais": lugares}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"[Brasil API/lugares] {e}")
        raise HTTPException(status_code=502, detail="Erro ao consultar Brasil API.")


@router.get("/periodos-voo")
def obter_periodos_voo():
    """
    Sugestões de período para voo.
    """
    try:
        periodos = _svc().obter_periodos_voo()
        return {"sucesso": True, "periodos": periodos}
    except Exception as e:
        logger.error(f"[Brasil API/periodos-voo] {e}")
        raise HTTPException(status_code=502, detail="Erro ao consultar períodos de voo.")
