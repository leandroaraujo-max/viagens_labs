"""
Serviço de vouchers.

Fluxo:
  1. Agência vencedora faz upload do voucher (PDF/imagem) via endpoint.
  2. Arquivo salvo em  frontend/vouchers/{protocolo}/{tipo}.{ext}
  3. Registro criado/atualizado em `vouchers` (ORM).
  4. Após upload, verifica se TODOS os vouchers esperados chegaram.
     Se sim: solicitação → CONCLUIDA + e-mails viajante + setor.
"""

import os
import logging
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.orm.models import SolicitacaoModel, VoucherModel

logger = logging.getLogger(__name__)

# Mapeamento tipo_servico → tipo_voucher esperado
_TIPOS_SERVICO_VOUCHER: dict[str, str] = {
    "Aereo":       "aereo",
    "Hospedagem":  "hospedagem",
    "Carro":       "carro",
    "Rodoviario":  "rodoviario",
}

# Diretório base onde os vouchers ficam (relativo à raiz do projeto)
_VOUCHERS_BASE = Path(__file__).resolve().parents[2] / "frontend" / "vouchers"


class VoucherService:

    # ── Upload de voucher ──────────────────────────────────────────────────────

    def registrar_voucher(
        self,
        db: Session,
        solicitacao: SolicitacaoModel,
        tipo_voucher: str,
        arquivo_bytes: bytes,
        filename: str,
    ) -> VoucherModel:
        """
        Persiste o arquivo no disco e cria/atualiza o registro na tabela vouchers.
        Retorna o VoucherModel salvo.
        Levanta ValueError para entradas inválidas.
        """
        tipo_voucher = tipo_voucher.lower().strip()
        tipos_validos = set(_TIPOS_SERVICO_VOUCHER.values())
        if tipo_voucher not in tipos_validos:
            raise ValueError(f"tipo_voucher inválido: {tipo_voucher}. Esperados: {tipos_validos}")

        # Garante extensão segura (só pdf / jpg / png)
        ext = Path(filename).suffix.lower()
        if ext not in {".pdf", ".jpg", ".jpeg", ".png"}:
            ext = ".pdf"

        # Cria pasta e salva arquivo
        pasta = _VOUCHERS_BASE / solicitacao.protocolo
        pasta.mkdir(parents=True, exist_ok=True)
        caminho_relativo = f"{solicitacao.protocolo}/{tipo_voucher}{ext}"
        caminho_absoluto = _VOUCHERS_BASE / f"{tipo_voucher}{ext}"
        caminho_absoluto = pasta / f"{tipo_voucher}{ext}"
        caminho_absoluto.write_bytes(arquivo_bytes)

        # Upsert no banco
        voucher = (
            db.query(VoucherModel)
            .filter_by(solicitacao_id=solicitacao.id, tipo_voucher=tipo_voucher)
            .first()
        )
        if voucher:
            voucher.caminho_arquivo = caminho_relativo
            voucher.data_criacao    = datetime.now(timezone.utc)
        else:
            voucher = VoucherModel(
                solicitacao_id  = solicitacao.id,
                tipo_voucher    = tipo_voucher,
                caminho_arquivo = caminho_relativo,
            )
            db.add(voucher)

        db.flush()
        logger.info(f"[Voucher] {solicitacao.protocolo} — {tipo_voucher} salvo em {caminho_relativo}")

        # Verifica se todos os vouchers necessários chegaram
        self._verificar_conclusao_vouchers(db, solicitacao)
        return voucher

    # ── Verificação de conclusão ───────────────────────────────────────────────

    def _verificar_conclusao_vouchers(self, db: Session, solicitacao: SolicitacaoModel) -> None:
        """Se todos os vouchers esperados chegaram, move para CONCLUIDA e notifica."""
        servicos = [s.strip() for s in (solicitacao.tipo_servico or "").split(",")]
        esperados = {_TIPOS_SERVICO_VOUCHER[s] for s in servicos if s in _TIPOS_SERVICO_VOUCHER}

        if not esperados:
            return

        presentes = {
            v.tipo_voucher
            for v in db.query(VoucherModel)
            .filter_by(solicitacao_id=solicitacao.id)
            .all()
        }

        faltantes = esperados - presentes
        logger.debug(f"[Voucher] {solicitacao.protocolo} — esperados={esperados} presentes={presentes} faltantes={faltantes}")

        if faltantes:
            return

        # Todos chegaram → CONCLUIDA
        solicitacao.status = "CONCLUIDA"
        db.flush()
        logger.info(f"[Voucher] {solicitacao.protocolo} → CONCLUIDA (todos os vouchers recebidos)")

        try:
            from app.infrastructure.email_service import EmailService
            todos_vouchers = (
                db.query(VoucherModel)
                .filter_by(solicitacao_id=solicitacao.id)
                .all()
            )
            svc = EmailService()
            svc.enviar_email_vouchers_viajante(solicitacao, todos_vouchers)
            svc.enviar_email_conclusao_setor(solicitacao)
        except Exception as e:
            logger.error(f"[Voucher] Falha ao enviar e-mails de conclusão para {solicitacao.protocolo}: {e}")
