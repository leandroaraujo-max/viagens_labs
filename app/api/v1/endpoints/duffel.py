from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import logging

from app.infrastructure.duffel_service import DuffelService

router = APIRouter()
logger = logging.getLogger(__name__)


def _svc() -> DuffelService:
    try:
        return DuffelService()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ── Schemas ───────────────────────────────────────────────────────────────────

class BuscaVoosRequest(BaseModel):
    origem:         str
    destino:        str
    data_ida:       str               # YYYY-MM-DD
    data_volta:     Optional[str] = None
    adultos:        int = 1
    cabine:         Optional[str] = None   # economy | business | first
    exigir_bagagem: bool = False


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/lugares")
def buscar_lugares(q: str = Query(..., min_length=2, description="Nome de cidade ou aeroporto")):
    """
    Autocomplete de aeroportos e cidades via Duffel Places API.
    Retorna até 8 sugestões com código IATA.
    """
    try:
        lugares = _svc().buscar_lugares(q)
        return {"sucesso": True, "locais": lugares}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"[Duffel/lugares] {e}")
        raise HTTPException(status_code=502, detail="Erro ao consultar Duffel API.")


@router.post("/voos")
def buscar_voos(body: BuscaVoosRequest):
    """
    Busca ofertas de voo (Azul, GOL, LATAM).
    Valores financeiros não são retornados — preço é responsabilidade da agência.
    """
    try:
        opcoes = _svc().buscar_voos(
            origem=body.origem,
            destino=body.destino,
            data_ida=body.data_ida,
            data_volta=body.data_volta,
            adultos=body.adultos,
            cabine=body.cabine,
            exigir_bagagem=body.exigir_bagagem,
        )
        return {"sucesso": True, "opcoes": opcoes}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"[Duffel/voos] {e}")
        raise HTTPException(status_code=502, detail="Erro ao consultar Duffel API.")
