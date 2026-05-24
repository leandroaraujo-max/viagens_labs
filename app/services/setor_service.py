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
    "REPROVAR",
    "REENVIAR_AGENCIAS",
    # APROVAR_<AGENCIA> é dinâmica e validada separadamente por is_aprovar_dinamica
}

# Mapeamento status → ações permitidas (APROVAR_<AGENCIA> é validada dinamicamente)
ACOES_POR_STATUS = {
    "PENDENTE_PRE_APROVACAO_SETOR": {"PRE_APROVAR", "PRE_REPROVAR"},
    "AGUARDANDO_COTACAO":           {"REENVIAR_AGENCIAS"},
    "COTACAO_ENVIADA":              {"REENVIAR_AGENCIAS"},
    "PENDENTE_APROVACAO_SETOR_COTACAO": {"REPROVAR"},  # APROVAR_<AGENCIA> é dinâmica
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
        """Retorna (solicitacao, cotacao_1a, cotacao_2a, casamentos, todas_cotacoes).
        
        Os dois primeiros slots de cotação (cot_tastur/cot_kontrip nos campos legados)
        são preenchidos dinamicamente com as primeiras cotações encontradas,
        sem dependência de nomes hardcoded.
        """
        sol = db.query(SolicitacaoModel).filter(SolicitacaoModel.id == solicitacao_id).first()
        if not sol:
            return None, None, None, [], []

        cotacoes = (
            db.query(CotacaoModel)
            .filter(CotacaoModel.solicitacao_id == solicitacao_id)
            .all()
        )
        # Preenche os slots legados dinâmicamente (sem hardcoding de nome de agência)
        cot_1 = cotacoes[0] if len(cotacoes) > 0 else None
        cot_2 = cotacoes[1] if len(cotacoes) > 1 else None
        casamentos  = _casamento_svc.listar_casamentos_da_solicitacao(db, solicitacao_id)

        return sol, cot_1, cot_2, casamentos, cotacoes

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
        
        is_aprovar_dinamica = False
        agencia_nome_dinamica = None
        if acao.startswith("APROVAR_") and acao != "APROVAR_MANUAL":
            agencia_nome_dinamica = acao[len("APROVAR_"):]
            is_aprovar_dinamica = True

        if acao not in ACOES_VALIDAS and not is_aprovar_dinamica:
            raise ValueError(f"Ação '{acao}' desconhecida. Opções: {sorted(ACOES_VALIDAS)}")

        sol = db.query(SolicitacaoModel).filter(SolicitacaoModel.id == solicitacao_id).first()
        if not sol:
            raise ValueError(f"Solicitação {solicitacao_id} não encontrada.")

        permitidas = ACOES_POR_STATUS.get(sol.status, set())
        
        # Se for aprovação dinâmica e o status for PENDENTE_APROVACAO_SETOR_COTACAO, é permitido!
        permitido_status = acao in permitidas
        if not permitido_status and is_aprovar_dinamica and sol.status == "PENDENTE_APROVACAO_SETOR_COTACAO":
            permitido_status = True

        if not permitido_status:
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

        elif is_aprovar_dinamica:
            # Pegamos o nome exato da agência (ex: Tastur, Kontrip ou outra dinâmica)
            # Para manter capitalização correta, tentamos achar no banco de dados ou cotações
            agencia = agencia_nome_dinamica.title()
            cotacao_existente = db.query(CotacaoModel).filter(
                CotacaoModel.solicitacao_id == solicitacao_id
            ).all()
            for c in cotacao_existente:
                if c.agencia_nome.upper() == agencia_nome_dinamica:
                    agencia = c.agencia_nome
                    break
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
            self._reenviar_agencias(db, sol)

        db.commit()
        return {"protocolo": sol.protocolo, "status": sol.status, "acao": acao}

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _pre_aprovar(self, db: Session, sol: SolicitacaoModel) -> None:
        """Pré-aprova a solicitação e solicita cotações a todas as agências ativas via link token."""
        sol.status = "AGUARDANDO_COTACAO"
        db.flush()
        logger.info(f"[Setor] {sol.protocolo} pré-aprovado → AGUARDANDO_COTACAO")

        # Busca todas as agências ativas no banco
        from app.infrastructure.orm.models import AgenciaModel
        agencias = db.query(AgenciaModel).filter_by(ativo=True).all()
        if not agencias:
            logger.warning(f"[Setor] Nenhuma agência ativa no banco para {sol.protocolo}. Verifique o cadastro.")
            lista_agencias = []
        else:
            lista_agencias = [a.agencia_nome for a in agencias]

        tokens_dict = {}
        for ag_nome in lista_agencias:
            tok = self._criar_token_agencia(db, sol, ag_nome, "COTACAO")
            db.flush()
            tokens_dict[ag_nome] = tok.uuid

            # Registra tokens no GAS relay para acesso externo das agências
            try:
                from app.infrastructure.google_relay_service import get_relay
                relay = get_relay()
                if relay.disponivel():
                    relay.registrar_agencia(tok, sol)
            except Exception as e:
                logger.warning(f"[Setor] Falha ao registrar token da agência {ag_nome} no GAS: {e}")

        try:
            from app.infrastructure.email_service import EmailService
            EmailService().enviar_email_agencias_cotacao(sol, tokens_dict)
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

        # Notificar todas as agências perdedoras dinamicamente
        try:
            from app.infrastructure.email_service import EmailService
            svc = EmailService()
            svc.enviar_email_agencia_vencedora(sol, agencia_nome, tok_voucher.uuid)
            
            # Notifica as outras agências que cotaram ou que receberam token de cotação
            tokens_cotacao = db.query(TokenAgenciaModel).filter_by(solicitacao_id=sol.id, finalidade="COTACAO").all()
            outras_agencias = set(t.agencia_nome for t in tokens_cotacao if t.agencia_nome.lower() != agencia_nome.lower())
            for outra in outras_agencias:
                svc.enviar_email_agencia_perdedora(sol, outra)

            svc.enviar_email_viajante_aprovado(sol, agencia_nome)
        except Exception as e:
            logger.error(f"[Setor] Falha ao notificar partes em {sol.protocolo}: {e}")

    def _reenviar_agencias(self, db: Session, sol: SolicitacaoModel) -> None:
        """Reenvia pedido de cotação a todas as agências ativas."""
        logger.info(f"[Setor] Reenvio de cotação solicitado para {sol.protocolo}")
        
        # Buscar tokens existentes de COTACAO para esta solicitação
        tokens = db.query(TokenAgenciaModel).filter_by(solicitacao_id=sol.id, finalidade="COTACAO").all()
        tokens_dict = {t.agencia_nome: t.uuid for t in tokens}
        
        try:
            from app.infrastructure.email_service import EmailService
            EmailService().enviar_email_agencias_cotacao(sol, tokens_dict)
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
