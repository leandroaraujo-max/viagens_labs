"""
Integração com a Duffel Flights API — busca consultiva de voos.

Regras de negócio preservadas do GAS (AmadeusAPI.js):
  - Apenas Azul (AD), GOL (G3) e LATAM (LA/JJ) são exibidas.
  - Valores financeiros NÃO são retornados ao frontend.
    Preço é responsabilidade exclusiva da agência de viagens.
  - Máximo 10 opções por busca.
  - Se filtro de bagagem não retornar resultados, exibe todos.
"""
import logging
import requests
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Companhias permitidas — apenas aéreas com operação doméstica relevante
_CIAS_PERMITIDAS = {"AD", "G3", "LA", "JJ"}
_CIA_NOMES = {
    "AD": "Azul",
    "G3": "GOL",
    "LA": "LATAM",
    "JJ": "LATAM",
}


class DuffelService:

    def __init__(self):
        token = settings.DUFFEL_TOKEN
        if not token:
            raise RuntimeError("DUFFEL_TOKEN não configurado. Adicione ao arquivo .env")
        self._headers = {
            "Authorization":  f"Bearer {token}",
            "Duffel-Version": settings.DUFFEL_VERSION,
            "Accept":         "application/json",
            "Content-Type":   "application/json",
        }
        self._base = settings.DUFFEL_BASE_URL

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _get(self, path: str) -> dict:
        resp = requests.get(f"{self._base}{path}", headers=self._headers, timeout=15)
        data = resp.json()
        if "errors" in data:
            msgs = "; ".join(e.get("message", str(e)) for e in data["errors"])
            raise ValueError(f"Duffel API: {msgs}")
        return data

    def _post(self, path: str, body: dict) -> dict:
        resp = requests.post(f"{self._base}{path}", headers=self._headers,
                             json=body, timeout=20)
        data = resp.json()
        if "errors" in data:
            msgs = "; ".join(e.get("message", str(e)) for e in data["errors"])
            raise ValueError(f"Duffel API: {msgs}")
        return data

    # ── Resolução de IATA ─────────────────────────────────────────────────────

    def _resolver_iata(self, valor: str) -> str:
        """
        Aceita código IATA (3 letras) ou nome de cidade/aeroporto.
        Se for nome, resolve via Places API e retorna o primeiro código IATA.
        """
        v = valor.strip().upper()
        if len(v) == 3 and v.isalpha():
            return v
        logger.info(f'[Duffel] "{v}" não é IATA — resolvendo via Places...')
        data = self._get(f"/places/suggestions?query={requests.utils.quote(valor)}&locale=pt-BR")
        locais = [l for l in (data.get("data") or []) if l.get("iata_code")]
        if not locais:
            raise ValueError(
                f'"{valor}" não encontrado. Selecione uma cidade da lista de sugestões.'
            )
        iata = locais[0]["iata_code"].upper()
        logger.info(f'[Duffel] "{v}" resolvido → {iata} ({locais[0].get("name")})')
        return iata

    # ── Busca de lugares (autocomplete) ──────────────────────────────────────

    def buscar_lugares(self, termo: str) -> list[dict]:
        """
        Autocomplete de aeroportos e cidades.
        Endpoint: GET /places/suggestions?query={termo}
        """
        data = self._get(
            f"/places/suggestions?query={requests.utils.quote(termo)}&locale=pt-BR"
        )
        lugares = []
        for l in (data.get("data") or []):
            if not l.get("iata_code"):
                continue
            lugares.append({
                "iata_code":      l["iata_code"],
                "nome":           l.get("name", ""),
                "cidade":         l.get("city_name") or l.get("name", ""),
                "pais":           l.get("country_name", ""),
                "tipo":           "AEROPORTO" if l.get("type") == "airport" else "CIDADE",
                "nome_aeroporto": l.get("name", "") if l.get("type") == "airport" else "",
            })
            if len(lugares) >= 8:
                break
        return lugares

    # ── Busca de voos ─────────────────────────────────────────────────────────

    def buscar_voos(
        self,
        origem:         str,
        destino:        str,
        data_ida:       str,             # 'YYYY-MM-DD'
        data_volta:     Optional[str] = None,
        adultos:        int = 1,
        cabine:         Optional[str] = None,  # economy | business | first | None=todas
        exigir_bagagem: bool = False,
    ) -> list[dict]:
        """
        Busca ofertas de voo via Duffel.
        Retorna até 10 opções filtradas por companhia (Azul/GOL/LATAM).
        Valores financeiros OMITIDOS intencionalmente.
        """
        iata_origem  = self._resolver_iata(origem)
        iata_destino = self._resolver_iata(destino)

        slices = [{"origin": iata_origem, "destination": iata_destino, "departure_date": data_ida}]
        if data_volta:
            slices.append({"origin": iata_destino, "destination": iata_origem, "departure_date": data_volta})

        passengers = [{"type": "adult"} for _ in range(max(1, adultos))]
        body: dict = {"data": {"slices": slices, "passengers": passengers}}
        if cabine:
            body["data"]["cabin_class"] = cabine.lower()

        json_resp = self._post("/air/offer_requests?return_offers=true", body)
        offers_raw = (json_resp.get("data") or {}).get("offers") or []

        # Filtro: apenas companhias permitidas
        offers = [o for o in offers_raw if self._cia_codigo(o) in _CIAS_PERMITIDAS]

        # Filtro: bagagem despachada (opcional — se vazio, usa todos)
        if exigir_bagagem:
            com_bagagem = [o for o in offers if self._tem_bagagem(o)]
            if com_bagagem:
                offers = com_bagagem

        return [r for r in (self._mapear_oferta(o) for o in offers[:10]) if r]

    # ── Helpers internos ──────────────────────────────────────────────────────

    @staticmethod
    def _cia_codigo(offer: dict) -> str:
        try:
            seg = offer["slices"][0]["segments"][0]
            return (
                seg.get("marketing_carrier") or
                seg.get("operating_carrier") or {}
            ).get("iata_code", "").upper()
        except Exception:
            return ""

    @staticmethod
    def _tem_bagagem(offer: dict) -> bool:
        try:
            bags = offer["slices"][0]["segments"][0]["passengers"][0].get("baggages", [])
            return any(b.get("type") == "checked" and b.get("quantity", 0) > 0 for b in bags)
        except Exception:
            return False

    def _mapear_oferta(self, offer: dict) -> Optional[dict]:
        try:
            slice0   = offer["slices"][0]
            segs     = slice0["segments"]
            seg0     = segs[0]
            seg_last = segs[-1]
            cia_op   = seg0.get("operating_carrier") or seg0.get("marketing_carrier") or {}
            cia_mkt  = seg0.get("marketing_carrier") or {}
            cia_cod  = (cia_op.get("iata_code") or cia_mkt.get("iata_code") or "").upper()
            paradas  = len(segs) - 1

            bagagem = False
            try:
                bagagem = any(
                    any(b.get("type") == "checked" and b.get("quantity", 0) > 0
                        for b in (p.get("baggages") or []))
                    for p in (offer.get("passengers") or [])
                )
            except Exception:
                pass

            escalas = [
                {
                    "aeroporto": s["origin"]["iata_code"],
                    "cidade": (s["origin"].get("city") or {}).get("name") or s["origin"].get("name", ""),
                }
                for s in segs[1:]
            ]

            volta = None
            if len(offer["slices"]) > 1:
                sv    = offer["slices"][1]["segments"]
                sv_last = sv[-1]
                volta = {
                    "origem":  sv[0]["origin"]["iata_code"],
                    "destino": sv_last["destination"]["iata_code"],
                    "saida":   sv[0]["departing_at"],
                    "chegada": sv_last["arriving_at"],
                    "paradas": len(sv) - 1,
                    "escalas": [
                        {
                            "aeroporto": s["origin"]["iata_code"],
                            "cidade": (s["origin"].get("city") or {}).get("name") or s["origin"].get("name", ""),
                        }
                        for s in sv[1:]
                    ],
                }

            # ── Campos financeiros OMITIDOS intencionalmente ──
            return {
                "id":         offer["id"],
                "cia_codigo": cia_cod,
                "cia_nome":   _CIA_NOMES.get(cia_cod) or cia_op.get("name") or cia_mkt.get("name") or "",
                "numero_voo": (cia_mkt.get("iata_code") or "") + (seg0.get("marketing_carrier_flight_number") or ""),
                "origem":     seg0["origin"]["iata_code"],
                "destino":    seg_last["destination"]["iata_code"],
                "saida":      seg0["departing_at"],
                "chegada":    seg_last["arriving_at"],
                "duracao":    slice0.get("duration", ""),
                "paradas":    paradas,
                "escalas":    escalas,
                "bagagem":    bagagem,
                "volta":      volta,
            }
        except Exception as e:
            logger.warning(f"[Duffel] Erro ao mapear oferta: {e}")
            return None
