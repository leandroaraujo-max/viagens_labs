from fastapi import APIRouter, Query, HTTPException
from app.core.config import settings
import httpx

router = APIRouter()

@router.get("/sugestoes")
def sugestoes_hoteis(q: str = Query(..., min_length=2, description="Nome do hotel ou local")):
    """
    Proxy seguro para sugestões de hotéis via Google Places API.
    """
    if not settings.GOOGLE_PLACES_KEY:
        raise HTTPException(status_code=500, detail="Chave Google Places não configurada.")
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": q,
        "types": "establishment",
        "key": settings.GOOGLE_PLACES_KEY,
        "language": "pt-BR"
    }
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(url, params=params)
            data = resp.json()
        if resp.status_code != 200 or "predictions" not in data:
            raise HTTPException(status_code=502, detail="Erro ao consultar Google Places.")
        # Retorna apenas os campos relevantes para o frontend
        return [
            {
                "descricao": p.get("description"),
                "place_id": p.get("place_id")
            }
            for p in data["predictions"]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no proxy Google Places: {e}")
