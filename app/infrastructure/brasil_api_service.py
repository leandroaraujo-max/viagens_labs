"""
Integração com a Brasil API (Aeroportos/CPTEC) e Autocomplete de aeroportos brasileiros.
"""
import logging
import requests
import unicodedata
from app.core.config import settings

logger = logging.getLogger(__name__)

_AEROPORTOS_BRASIL = [
    {"iata": "GRU", "icao": "SBGR", "nome": "Aeroporto Internacional de Guarulhos", "cidade": "São Paulo", "estado": "SP"},
    {"iata": "CGH", "icao": "SBSP", "nome": "Aeroporto de Congonhas", "cidade": "São Paulo", "estado": "SP"},
    {"iata": "BSB", "icao": "SBBR", "nome": "Aeroporto Internacional de Brasília", "cidade": "Brasília", "estado": "DF"},
    {"iata": "GIG", "icao": "SBGL", "nome": "Aeroporto Internacional do Galeão", "cidade": "Rio de Janeiro", "estado": "RJ"},
    {"iata": "SDU", "icao": "SBRJ", "nome": "Aeroporto Santos Dumont", "cidade": "Rio de Janeiro", "estado": "RJ"},
    {"iata": "CNF", "icao": "SBCF", "nome": "Aeroporto Internacional de Confins", "cidade": "Belo Horizonte", "estado": "MG"},
    {"iata": "VCP", "icao": "SBKP", "nome": "Aeroporto Internacional de Viracopos", "cidade": "Campinas", "estado": "SP"},
    {"iata": "SSA", "icao": "SBSV", "nome": "Aeroporto Internacional de Salvador", "cidade": "Salvador", "estado": "BA"},
    {"iata": "REC", "icao": "SBRF", "nome": "Aeroporto Internacional do Recife", "cidade": "Recife", "estado": "PE"},
    {"iata": "POA", "icao": "SBPA", "nome": "Aeroporto Internacional Salgado Filho", "cidade": "Porto Alegre", "estado": "RS"},
    {"iata": "FOR", "icao": "SBFZ", "nome": "Aeroporto Internacional de Fortaleza", "cidade": "Fortaleza", "estado": "CE"},
    {"iata": "CWB", "icao": "SBCT", "nome": "Aeroporto Internacional de Curitiba", "cidade": "Curitiba", "estado": "PR"},
    {"iata": "FLN", "icao": "SBFL", "nome": "Aeroporto Internacional de Florianópolis", "cidade": "Florianópolis", "estado": "SC"},
    {"iata": "BEL", "icao": "SBBE", "nome": "Aeroporto Internacional de Belém", "cidade": "Belém", "estado": "PA"},
    {"iata": "MAO", "icao": "SBEG", "nome": "Aeroporto Internacional de Manaus", "cidade": "Manaus", "estado": "AM"},
    {"iata": "GYN", "icao": "SBGO", "nome": "Aeroporto de Goiânia", "cidade": "Goiânia", "estado": "GO"},
    {"iata": "VIX", "icao": "SBVT", "nome": "Aeroporto de Vitória", "cidade": "Vitória", "estado": "ES"},
    {"iata": "CGB", "icao": "SBCY", "nome": "Aeroporto Internacional de Cuiabá", "cidade": "Cuiabá", "estado": "MT"},
    {"iata": "CGR", "icao": "SBCG", "nome": "Aeroporto Internacional de Campo Grande", "cidade": "Campo Grande", "estado": "MS"},
    {"iata": "NAT", "icao": "SBSG", "nome": "Aeroporto Internacional de Natal", "cidade": "Natal", "estado": "RN"},
    {"iata": "MCZ", "icao": "SBMO", "nome": "Aeroporto Internacional de Maceió", "cidade": "Maceió", "estado": "AL"},
    {"iata": "SLZ", "icao": "SBSL", "nome": "Aeroporto Internacional de São Luís", "cidade": "São Luís", "estado": "MA"},
    {"iata": "AJU", "icao": "SBAR", "nome": "Aeroporto de Aracaju", "cidade": "Aracaju", "estado": "SE"},
    {"iata": "JPA", "icao": "SBJP", "nome": "Aeroporto Internacional de João Pessoa", "cidade": "João Pessoa", "estado": "PB"},
    {"iata": "THE", "icao": "SBTE", "nome": "Aeroporto de Teresina", "cidade": "Teresina", "estado": "PI"},
    {"iata": "PMW", "icao": "SBPJ", "nome": "Aeroporto de Palmas", "cidade": "Palmas", "estado": "TO"},
    {"iata": "PVH", "icao": "SBPV", "nome": "Aeroporto Internacional de Porto Velho", "cidade": "Porto Velho", "estado": "RO"},
    {"iata": "RBR", "icao": "SBRB", "nome": "Aeroporto Internacional de Rio Branco", "cidade": "Rio Branco", "estado": "AC"},
    {"iata": "BVB", "icao": "SBBV", "nome": "Aeroporto Internacional de Boa Vista", "cidade": "Boa Vista", "estado": "RR"},
    {"iata": "MCP", "icao": "SBMQ", "nome": "Aeroporto Internacional de Macapá", "cidade": "Macapá", "estado": "AP"},
    {"iata": "RAO", "icao": "SBRP", "nome": "Aeroporto de Ribeirão Preto", "cidade": "Ribeirão Preto", "estado": "SP"},
    {"iata": "UDI", "icao": "SBUL", "nome": "Aeroporto de Uberlândia", "cidade": "Uberlândia", "estado": "MG"},
    {"iata": "LDB", "icao": "SBLO", "nome": "Aeroporto de Londrina", "cidade": "Londrina", "estado": "PR"},
    {"iata": "JOI", "icao": "SBJV", "nome": "Aeroporto de Joinville", "cidade": "Joinville", "estado": "SC"},
    {"iata": "NVT", "icao": "SBNF", "nome": "Aeroporto Internacional de Navegantes", "cidade": "Navegantes", "estado": "SC"},
]

def remover_acentos(texto: str) -> str:
    """Remove acentos de uma string e converte para maiúsculo para facilitar a busca."""
    if not texto:
        return ""
    texto = texto.upper()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

class BrasilApiService:
    def __init__(self):
        self._base_url = settings.BRASIL_API_BASE_URL

    def buscar_lugares(self, termo: str) -> list[dict]:
        termo_clean = termo.strip().upper()
        if not termo_clean:
            return []
            
        # O pulo do gato: cria a versão sem acento do que o usuário digitou
        termo_sem_acento = remover_acentos(termo_clean)

        # Se for um código ICAO, faz requisição para a Brasil API para obter as condições climáticas
        brasil_api_info = None
        if len(termo_clean) == 4:
            try:
                resp = requests.get(f"{self._base_url}/cptec/v1/clima/aeroporto/{termo_clean}", timeout=5)
                if resp.status_code == 200:
                    brasil_api_info = resp.json()
            except Exception as e:
                logger.error(f"[Brasil API] Erro ao validar ICAO {termo_clean}: {e}")

        # Filtra na nossa base de dados local (Ignorando acentos)
        resultados = []
        for ap in _AEROPORTOS_BRASIL:
            # Tira o acento do nome da cidade e do nome do aeroporto do banco
            cidade_sem_acento = remover_acentos(ap["cidade"])
            nome_sem_acento = remover_acentos(ap["nome"])
            
            # Compara tudo sem acento!
            if (termo_sem_acento in ap["iata"].upper() or 
                termo_sem_acento in ap["icao"].upper() or 
                termo_sem_acento in nome_sem_acento or 
                termo_sem_acento in cidade_sem_acento):
                
                # Se obtivemos dados climáticos da Brasil API para este aeroporto específico
                clima_msg = ""
                if brasil_api_info and brasil_api_info.get("codigo_icao") == ap["icao"]:
                    cond = brasil_api_info.get("condicao_desc")
                    temp = brasil_api_info.get("temp")
                    if cond != "undefined" and temp != "undefined":
                        clima_msg = f" ({cond}, {temp}°C)"
                
                resultados.append({
                    "iata_code": ap["iata"],
                    "nome": ap["nome"] + clima_msg,
                    "cidade": f"{ap['cidade']}/{ap['estado']}",
                    "pais": "Brasil",
                    "tipo": "AEROPORTO",
                    "nome_aeroporto": ap["nome"],
                })

        # Se não encontrou na lista local mas a Brasil API confirmou a existência do código ICAO
        if not resultados and brasil_api_info and "codigo_icao" in brasil_api_info:
            icao = brasil_api_info["codigo_icao"]
            iata = icao[1:] if len(icao) == 4 else icao
            resultados.append({
                "iata_code": iata,
                "nome": f"Aeroporto {icao}",
                "cidade": "Aeroporto validado via Brasil API",
                "pais": "Brasil",
                "tipo": "AEROPORTO",
                "nome_aeroporto": f"Aeroporto {icao}",
            })

        return resultados[:8]

    def obter_periodos_voo(self) -> list[dict]:
        """
        Retorna as sugestões de período permitidas para preferência de voo.
        """
        return [
            {"id": "manha", "nome": "Manhã", "horario_inicio": "06:00", "horario_fim": "12:00", "emoji": "🌅"},
            {"id": "tarde", "nome": "Tarde", "horario_inicio": "12:00", "horario_fim": "18:00", "emoji": "☀️"},
            {"id": "noite", "nome": "Noite", "horario_inicio": "18:00", "horario_fim": "23:59", "emoji": "🌙"},
            {"id": "madrugada", "nome": "Madrugada", "horario_inicio": "00:00", "horario_fim": "06:00", "emoji": "🌌"},
        ]
