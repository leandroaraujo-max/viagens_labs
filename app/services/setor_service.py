import uuid as _uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.infrastructure.orm.models import SolicitacaoModel, CotacaoModel, TokenAgenciaModel
from app.services.casamento_service import CasamentoService

logger = logging.getLogger(__name__)
_casamento_svc = CasamentoService()

# Statuses visíveis no painel do setor
STATUSES_SETOR = {
    "AGUARDANDO_N1",
    "AGUARDANDO_N2",
    "PENDENTE_PRE_APROVACAO_SETOR",
    "AGUARDANDO_COTACAO",
    "COTACAO_ENVIADA",
    "PENDENTE_APROVACAO_SETOR_COTACAO",
    "APROVADA_AGUARDANDO_VOUCHER",
    "PENDENTE_APROVACAO_MANUAL",
    "CONCLUIDA",
    "REPROVADA",
    "CADEIA_INCOMPLETA",
}

ACOES_VALIDAS = {
    "PRE_APROVAR",
    "PRE_REPROVAR",
    "APROVAR_TASTUR",
    "APROVAR_KONTRIP",
    "REPROVAR",
    "REENVIAR_AGENCIAS",
}

# Mapeamento status → ações permitidas
ACOES_POR_STATUS = {
    "PENDENTE_PRE_APROVACAO_SETOR": {"PRE_APROVAR", "PRE_REPROVAR"},
    "AGUARDANDO_COTACAO":           {"REENVIAR_AGENCIAS"},
    "COTACAO_ENVIADA":              {"REENVIAR_AGENCIAS"},
    "PENDENTE_APROVACAO_SETOR_COTACAO": {"APROVAR_TASTUR", "APROVAR_KONTRIP", "REPROVAR"},
}


class SetorService:

    # ── Listagem ──────────────────────────────────────────────────────────────

    def listar_solicitacoes(
        self,
        db: Session,
        status_filtro: str | None = None,
        periodo_dias: int | None = None,
        agencia_filtro: str | None = None,
        busca: str | None = None,
    ):
        from datetime import datetime, timedelta
        query = db.query(SolicitacaoModel)

        if status_filtro:
            query = query.filter(SolicitacaoModel.status == status_filtro)
        if periodo_dias:
            limite = datetime.now() - timedelta(days=periodo_dias)
            query = query.filter(SolicitacaoModel.data_criacao >= limite)
        if agencia_filtro:
            query = query.filter(SolicitacaoModel.agencia_vencedora == agencia_filtro)
        if busca:
            termo = f"%{busca}%"
            query = query.filter(
                SolicitacaoModel.protocolo.ilike(termo)
                | SolicitacaoModel.solicitante_username.ilike(termo)
                | SolicitacaoModel.destino_cidade.ilike(termo)
            )

        return query.order_by(SolicitacaoModel.data_criacao.desc()).all()

    def get_solicitacao(self, db: Session, solicitacao_id: int):
        """Retorna (solicitacao, cotacao_tastur, cotacao_kontrip, casamentos)."""
        sol = db.query(SolicitacaoModel).filter(SolicitacaoModel.id == solicitacao_id).first()
        if not sol:
            return None, None, None, []

        cotacoes = (
            db.query(CotacaoModel)
            .filter(CotacaoModel.solicitacao_id == solicitacao_id)
            .all()
        )
        cot_tastur  = next((c for c in cotacoes if c.agencia_nome == "Tastur"),  None)
        cot_kontrip = next((c for c in cotacoes if c.agencia_nome == "Kontrip"), None)
        casamentos  = _casamento_svc.listar_casamentos_da_solicitacao(db, solicitacao_id)

        return sol, cot_tastur, cot_kontrip, casamentos

    # ── Executar ação ─────────────────────────────────────────────────────────

    def executar_acao(
        self,
        db: Session,
        solicitacao_id: int,
        acao: str,
        observacao: str = "",
    ) -> dict:
        """
        Executa uma ação do setor sobre a solicitação.

        Retorna dict com 'protocolo', 'status', 'acao' ou lança ValueError em caso de erro.
        """
        acao = acao.upper()
        if acao not in ACOES_VALIDAS:
            raise ValueError(f"Ação '{acao}' desconhecida. Opções: {sorted(ACOES_VALIDAS)}")

        sol = db.query(SolicitacaoModel).filter(SolicitacaoModel.id == solicitacao_id).first()
        if not sol:
            raise ValueError(f"Solicitação {solicitacao_id} não encontrada.")

        permitidas = ACOES_POR_STATUS.get(sol.status, set())
        if acao not in permitidas:
            raise ValueError(
                f"Ação '{acao}' não é permitida no status '{sol.status}'. "
                f"Permitidas: {sorted(permitidas) or 'nenhuma'}"
            )

        if acao == "PRE_APROVAR":
            self._pre_aprovar(db, sol)

        elif acao == "PRE_REPROVAR":
            sol.status = "REPROVADA"
            logger.info(f"[Setor] {sol.protocolo} pré-reprovado. Obs: {observacao}")
            try:
                from app.infrastructure.email_service import EmailService
                EmailService().enviar_email_reprovacao_viajante(sol, etapa="Setor (Pré-Aprovação)", motivo=observacao)
            except Exception as e:
                logger.error(f"[Setor] Falha ao notificar viajante sobre pré-reprovação em {sol.protocolo}: {e}")

        elif acao in ("APROVAR_TASTUR", "APROVAR_KONTRIP"):
            agencia = "Tastur" if acao == "APROVAR_TASTUR" else "Kontrip"
            self._aprovar_agencia(db, sol, agencia)

        elif acao == "REPROVAR":
            sol.status = "REPROVADA"
            logger.info(f"[Setor] {sol.protocolo} reprovado após cotações. Obs: {observacao}")
            try:
                from app.infrastructure.email_service import EmailService
                EmailService().enviar_email_reprovacao_viajante(sol, etapa="Setor", motivo=observacao)
            except Exception as e:
                logger.error(f"[Setor] Falha ao notificar viajante sobre reprovação em {sol.protocolo}: {e}")

        elif acao == "REENVIAR_AGENCIAS":
            self._reenviar_agencias(sol)

        db.commit()
        return {"protocolo": sol.protocolo, "status": sol.status, "acao": acao}

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _pre_aprovar(self, db: Session, sol: SolicitacaoModel) -> None:
        """Pré-aprova a solicitação e solicita cotações às duas agências via link token."""
        sol.status = "AGUARDANDO_COTACAO"
        db.flush()
        logger.info(f"[Setor] {sol.protocolo} pré-aprovado → AGUARDANDO_COTACAO")

        # Cria token independente por agência (único para esta solicitação)
        tok_tastur  = self._criar_token_agencia(db, sol, "Tastur",  "COTACAO")
        tok_kontrip = self._criar_token_agencia(db, sol, "Kontrip", "COTACAO")
        db.flush()

        try:
            from app.infrastructure.email_service import EmailService
            EmailService().enviar_email_agencias_cotacao(sol, {
                "Tastur":  tok_tastur.uuid,
                "Kontrip": tok_kontrip.uuid,
            })
        except Exception as e:
            logger.error(f"[Setor] Falha ao enviar e-mail às agências para {sol.protocolo}: {e}")

    def _aprovar_agencia(self, db: Session, sol: SolicitacaoModel, agencia_nome: str) -> None:
        """Escolhe a agência vencedora → status APROVADA_AGUARDANDO_VOUCHER. CONCLUIDA só após vouchers."""
        sol.status = "APROVADA_AGUARDANDO_VOUCHER"
        sol.agencia_vencedora = agencia_nome
        db.flush()
        logger.info(f"[Setor] {sol.protocolo} → APROVADA_AGUARDANDO_VOUCHER (agência: {agencia_nome})")

        # Token de voucher para a vencedora (TTL 7 dias)
        tok_voucher = self._criar_token_agencia(db, sol, agencia_nome, "VOUCHER")
        db.flush()

        agencia_perdedora = "Kontrip" if agencia_nome == "Tastur" else "Tastur"
        try:
            from app.infrastructure.email_service import EmailService
            svc = EmailService()
            svc.enviar_email_agencia_vencedora(sol, agencia_nome, tok_voucher.uuid)
            svc.enviar_email_agencia_perdedora(sol, agencia_perdedora)
            svc.enviar_email_viajante_aprovado(sol, agencia_nome)
        except Exception as e:
            logger.error(f"[Setor] Falha ao notificar partes em {sol.protocolo}: {e}")

    def _reenviar_agencias(self, sol: SolicitacaoModel) -> None:
        """Reenvia pedido de cotação às duas agências sem alterar o status."""
        logger.info(f"[Setor] Reenvio de cotação solicitado para {sol.protocolo}")
        try:
            from app.infrastructure.email_service import EmailService
            EmailService().enviar_email_agencias_cotacao(sol)
        except Exception as e:
            logger.error(f"[Setor] Falha ao reenviar e-mails para {sol.protocolo}: {e}")

    def _criar_token_agencia(
        self, db: Session, sol: SolicitacaoModel, agencia_nome: str, finalidade: str
    ) -> TokenAgenciaModel:
        """Cria um token de acesso por link para a agência (sem necessidade de login)."""
        ttl_dias = 7 if finalidade == "COTACAO" else 14
        tok = TokenAgenciaModel(
            uuid=str(_uuid.uuid4()),
            solicitacao_id=sol.id,
            agencia_nome=agencia_nome,
            finalidade=finalidade,
            status="PENDENTE",
            data_expiracao=datetime.now() + timedelta(days=ttl_dias),
        )
        db.add(tok)
        return tok
