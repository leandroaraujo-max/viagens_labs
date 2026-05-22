"""
Integração com o Google Apps Script Web App usado como relay externo de aprovações.

O GAS atua como fila pública (Google Sheets) acessível de qualquer lugar.
O FastAPI lê/escreve via HTTP simples — sem Google SDK, sem service account.

Fluxo:
  1. FastAPI cria token → chama registrar_aprovacao() → GAS grava na planilha
  2. E-mail enviado ao aprovador com link GAS_RELAY_URL?token=UUID
  3. Aprovador abre no celular/browser → GAS serve o portal HTML → aprova/reprova
  4. Scheduler (aprovacao_relay_scheduler) faz poll() a cada 60s
  5. Decisão encontrada → processar_resposta() no AprovacaoService → avança workflow
  6. marcar_processado() chamado para evitar reprocessamento
"""
import logging
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleRelayService:
    """Serviço de integração com o GAS Web App relay de aprovações."""

    def __init__(self):
        self.url    = getattr(settings, 'GAS_RELAY_URL', '').strip()
        self.secret = getattr(settings, 'GAS_SECRET', '').strip()

    def disponivel(self) -> bool:
        """Retorna True se GAS_RELAY_URL e GAS_SECRET estão configurados."""
        return bool(self.url and self.secret)

    def _post(self, payload: dict) -> dict | None:
        if not self.disponivel():
            return None
        try:
            resp = requests.post(
                self.url,
                json=payload,
                timeout=20,
                allow_redirects=True,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.warning('[GAS] Timeout na chamada ao relay.')
            return None
        except Exception as exc:
            logger.error(f'[GAS] Erro na chamada: {exc}')
            return None

    def registrar_aprovacao(self, token_model, solicitacao) -> bool:
        """
        Registra uma aprovação pendente no GAS para que o aprovador possa
        acessar o portal pelo celular (fora da intranet).
        """
        if not self.disponivel():
            return False

        payload = {
            'action':         'registrar',
            'secret':         self.secret,
            'token':          token_model.uuid,
            'protocolo':      solicitacao.protocolo,
            'viajante_nome':  getattr(solicitacao, 'viajante_nome', '') or '',
            'destino_cidade': getattr(solicitacao, 'destino_cidade', '') or '',
            'destino_estado': getattr(solicitacao, 'destino_estado', '') or '',
            'data_ida':       (
                solicitacao.data_ida.strftime('%d/%m/%Y')
                if getattr(solicitacao, 'data_ida', None) else ''
            ),
            'data_volta':     (
                solicitacao.data_volta.strftime('%d/%m/%Y')
                if getattr(solicitacao, 'data_volta', None) else ''
            ),
            'tipo_servico':   getattr(solicitacao, 'tipo_servico', '') or '',
            'motivo':         getattr(solicitacao, 'motivo_viagem', '') or '',
            'nivel':          token_model.nivel,
            'nome_aprovador': token_model.nome_aprovador or '',
            'expirado_em':    token_model.data_expiracao.strftime('%d/%m/%Y %H:%M'),
        }

        result = self._post(payload)
        ok = bool(result and result.get('ok'))
        if ok:
            logger.info(
                f'[GAS] Aprovação registrada: {token_model.uuid[:8]}… '
                f'({token_model.nivel} — {solicitacao.protocolo})'
            )
        else:
            logger.warning(f'[GAS] Falha ao registrar aprovação: {result}')
        return ok

    def poll_decisoes(self) -> list[dict]:
        """
        Retorna lista de decisões não processadas vindas do GAS.
        Cada item contém: token, decisao (APROVADO|REPROVADO), observacao,
        respondido_em, protocolo, nivel.
        """
        result = self._post({'action': 'poll', 'secret': self.secret})
        if not result or not result.get('ok'):
            if result:
                logger.warning(f'[GAS] poll retornou erro: {result.get("msg")}')
            return []
        return result.get('decisoes', [])

    def marcar_processado(self, token_uuid: str) -> bool:
        """Marca uma decisão como processada no GAS (evita reprocessamento)."""
        result = self._post({
            'action': 'processar',
            'secret': self.secret,
            'token':  token_uuid,
        })
        return bool(result and result.get('ok'))

    def link_aprovacao(self, token_uuid: str) -> str:
        """
        Retorna a URL do portal de aprovação.
        Se GAS disponível → URL pública do GAS.
        Caso contrário   → URL interna (fallback).
        """
        if self.disponivel():
            return f'{self.url}?token={token_uuid}'
        base = getattr(settings, 'BASE_URL_APROVACAO', settings.BASE_URL)
        return f'{base}/portal_aprovacao.html?token={token_uuid}'

    # ── Agências ──────────────────────────────────────────────────────────────

    def registrar_agencia(self, token_agencia, solicitacao) -> bool:
        """Registra token de cotação no GAS para acesso externo da agência."""
        if not self.disponivel():
            return False
        payload = {
            'action':                 'registrar_agencia',
            'secret':                 self.secret,
            'token':                  token_agencia.uuid,
            'protocolo':              solicitacao.protocolo,
            'agencia_nome':           token_agencia.agencia_nome,
            'tipo_servico':           getattr(solicitacao, 'tipo_servico', '') or '',
            'solicitante':            getattr(solicitacao, 'solicitante_username', '') or '',
            'destino':                f"{getattr(solicitacao,'destino_cidade','')} / {getattr(solicitacao,'destino_estado','')}",
            'data_ida':               solicitacao.data_ida.strftime('%d/%m/%Y') if getattr(solicitacao, 'data_ida', None) else '',
            'data_volta':             solicitacao.data_volta.strftime('%d/%m/%Y') if getattr(solicitacao, 'data_volta', None) else '',
            'aereo_periodo':          getattr(solicitacao, 'aereo_periodo_preferido', '') or '',
            'aereo_trecho':           getattr(solicitacao, 'aereo_tipo_trecho', '') or '',
            'bagagem_extra':          bool(getattr(solicitacao, 'bagagem_extra', False)),
            'assento':                getattr(solicitacao, 'assento_especial', '') or '',
            'rodov_periodo':          getattr(solicitacao, 'rodov_periodo_preferido', '') or '',
            'rodov_tipo':             getattr(solicitacao, 'rodov_tipo_onibus', '') or '',
            'hotel_nome_pref':        getattr(solicitacao, 'preferencia_hotel_nome', '') or '',
            'carro_retirada_cidade':  getattr(solicitacao, 'carro_cidade_retirada', '') or '',
            'carro_devolucao_cidade': getattr(solicitacao, 'carro_cidade_devolucao', '') or '',
            'observacoes_viajante':   getattr(solicitacao, 'observacoes_viajante', '') or '',
            'expirado_em':            token_agencia.data_expiracao.isoformat(),
        }
        result = self._post(payload)
        ok = bool(result and result.get('ok'))
        if not ok:
            logger.warning(f'[GAS] Falha ao registrar agência {token_agencia.agencia_nome}: {result}')
        return ok

    def poll_cotacoes(self) -> list[dict]:
        """Retorna cotações de agências não processadas vindas do GAS."""
        result = self._post({'action': 'poll_cotacoes', 'secret': self.secret})
        if not result or not result.get('ok'):
            if result:
                logger.warning(f'[GAS] poll_cotacoes retornou erro: {result.get("msg")}')
            return []
        return result.get('cotacoes', [])

    def marcar_cotacao_processada(self, token_uuid: str) -> bool:
        """Marca cotação de agência como processada no GAS."""
        result = self._post({'action': 'processar_cotacao', 'secret': self.secret, 'token': token_uuid})
        return bool(result and result.get('ok'))

    def link_agencia(self, token_uuid: str) -> str:
        """URL pública do portal de cotação da agência no GAS."""
        if self.disponivel():
            return f'{self.url}?agencia_token={token_uuid}'
        base = getattr(settings, 'BASE_URL_AGENCIA', settings.BASE_URL)
        return f'{base}/agencia.html?token={token_uuid}'


# Singleton — importado pelos outros módulos
_relay = GoogleRelayService()


def get_relay() -> GoogleRelayService:
    return _relay
