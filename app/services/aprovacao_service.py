import uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.infrastructure.orm.models import TokenAprovacaoModel, SolicitacaoModel
from app.services.casamento_service import CasamentoService
from app.infrastructure.bigquery_service import BigQueryService
from app.core.config import settings

logger = logging.getLogger(__name__)
_casamento_svc = CasamentoService()

# Instância BQ para verificação de situação dos aprovadores
_bq_service = BigQueryService(
    project_id="maga-bigdata",
    table_assignee="maga-bigdata.kirk.assignee",
    table_funcionarios="maga-bigdata.mlpap.mag_v_funcionarios_ativos",
)

# Valores de SITUACAO que indicam ausência por férias
_SITUACOES_FERIAS = {"férias", "ferias"}


class AprovacaoService:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # Iniciar fluxo após criação da solicitação
    # -------------------------------------------------------------------------

    def iniciar_fluxo_aprovacao(self, solicitacao: SolicitacaoModel) -> None:
        """
        Gera token de aprovação e envia e-mail.
        Se o N1 estiver de Férias (verificado via BigQuery), o fluxo é redirecionado
        diretamente ao N2 sem passar pelo N1.
        """
        if not solicitacao.aprovador_n1_email:
            logger.warning(
                f"Solicitação {solicitacao.protocolo}: aprovador N1 não informado. "
                "Marcando CADEIA_INCOMPLETA."
            )
            solicitacao.status = "CADEIA_INCOMPLETA"
            self.db.commit()
            return

        # ── Verificar se N1 está de Férias via BigQuery ──────────────────────
        if self._aprovador_esta_de_ferias(solicitacao.aprovador_n1_email):
            logger.info(
                f"Solicitação {solicitacao.protocolo}: N1 '{solicitacao.aprovador_n1_nome}' "
                f"está de Férias. Redirecionando aprovação diretamente ao N2."
            )
            if not solicitacao.aprovador_n2_email:
                logger.warning(
                    f"Solicitação {solicitacao.protocolo}: N1 de Férias e N2 não informado. "
                    "Marcando CADEIA_INCOMPLETA."
                )
                solicitacao.status = "CADEIA_INCOMPLETA"
                self.db.commit()
                return

            # Vai direto para N2 — quando ele aprovar, segue o fluxo normal de N2
            solicitacao.status = "AGUARDANDO_N2"
            self.db.flush()
            token = self._criar_token(solicitacao, "N2")
            self.db.commit()
            self._enviar_email_aprovacao(solicitacao, token)
            return
        # ─────────────────────────────────────────────────────────────────────

        token = self._criar_token(solicitacao, "N1")
        self.db.commit()
        self._enviar_email_aprovacao(solicitacao, token)

    # -------------------------------------------------------------------------
    # Leitura de detalhes pelo token
    # -------------------------------------------------------------------------

    def get_detalhes_por_token(self, token_uuid: str) -> dict | None:
        token = (
            self.db.query(TokenAprovacaoModel)
            .filter(TokenAprovacaoModel.uuid == token_uuid)
            .first()
        )
        if not token:
            return None

        solicitacao = (
            self.db.query(SolicitacaoModel)
            .filter_by(id=token.solicitacao_id)
            .first()
        )

        expirado = datetime.now() > token.data_expiracao

        return {
            "token_uuid": token.uuid,
            "nivel": token.nivel,
            "status_token": token.status,
            "nome_aprovador": token.nome_aprovador,
            "email_aprovador": token.email_aprovador,
            "data_expiracao": token.data_expiracao.isoformat(),
            "expirado": expirado,
            "solicitacao": {
                "protocolo": solicitacao.protocolo,
                "solicitante_username": solicitacao.solicitante_username,
                "destino_cidade": solicitacao.destino_cidade,
                "destino_estado": solicitacao.destino_estado,
                "data_ida": solicitacao.data_ida.strftime("%d/%m/%Y"),
                "data_volta": solicitacao.data_volta.strftime("%d/%m/%Y") if solicitacao.data_volta else None,
                "motivo_viagem": solicitacao.motivo_viagem,
                "tipo_servico": solicitacao.tipo_servico.split(","),
                "classificacao": solicitacao.classificacao,
                "status": solicitacao.status,
                "antecedencia_dias": solicitacao.antecedencia_dias,
                "observacoes_viajante": solicitacao.observacoes_viajante,
            },
        }

    # -------------------------------------------------------------------------
    # Processar resposta do aprovador
    # -------------------------------------------------------------------------

    def processar_resposta(self, token_uuid: str, acao: str, observacao: str = "") -> dict | None:
        """
        Processa a aprovação ou reprovação. Retorna:
        - None        → token não encontrado
        - {'expirado': True} → token expirado
        - dict com protocolo/status → sucesso
        """
        token = (
            self.db.query(TokenAprovacaoModel)
            .filter(
                TokenAprovacaoModel.uuid == token_uuid,
                TokenAprovacaoModel.status == "PENDENTE",
            )
            .first()
        )

        if not token:
            return None

        if datetime.now() > token.data_expiracao:
            token.status = "EXPIRADO"
            self.db.commit()
            return {"expirado": True}

        solicitacao = (
            self.db.query(SolicitacaoModel)
            .filter_by(id=token.solicitacao_id)
            .first()
        )

        # Registrar decisão no token
        token.status = "APROVADO" if acao == "aprovar" else "REPROVADO"
        token.data_resposta = datetime.now()
        token.observacao_resposta = observacao

        if acao == "aprovar":
            self._processar_aprovacao(solicitacao, token)
        else:
            solicitacao.status = "REPROVADA"

        self.db.commit()

        # Notificar solicitante
        self._enviar_email_resultado(solicitacao, token.nivel, acao, token.nome_aprovador)

        return {
            "protocolo": solicitacao.protocolo,
            "status": solicitacao.status,
            "nivel": token.nivel,
            "acao": acao,
        }

    # -------------------------------------------------------------------------
    # Helpers internos
    # -------------------------------------------------------------------------

    def _processar_aprovacao(self, solicitacao: SolicitacaoModel, token: TokenAprovacaoModel) -> None:
        if token.nivel == "N1":
            if solicitacao.exige_aprovacao_diretoria:
                if solicitacao.aprovador_n2_email:
                    solicitacao.status = "AGUARDANDO_N2"
                    self.db.flush()
                    token_n2 = self._criar_token(solicitacao, "N2")
                    self.db.commit()
                    self._enviar_email_aprovacao(solicitacao, token_n2)
                else:
                    logger.warning(
                        f"Solicitação {solicitacao.protocolo} exige N2, mas e-mail N2 não cadastrado. "
                        "Marcando CADEIA_INCOMPLETA."
                    )
                    solicitacao.status = "CADEIA_INCOMPLETA"
            else:
                # N1 aprovou via fluxo comum → aguarda pré-aprovação do Setor
                solicitacao.status = "PENDENTE_PRE_APROVACAO_SETOR"
                self.db.flush()
                _casamento_svc.processar_casamentos(self.db, solicitacao)
                self._enviar_email_setor(solicitacao)

        elif token.nivel == "N2":
            # N2 aprovou (emergêncial) → aguarda pré-aprovação do Setor
            solicitacao.status = "PENDENTE_PRE_APROVACAO_SETOR"
            self.db.flush()
            _casamento_svc.processar_casamentos(self.db, solicitacao)
            self._enviar_email_setor(solicitacao)

    def _criar_token(self, solicitacao: SolicitacaoModel, nivel: str) -> TokenAprovacaoModel:
        if nivel == "N1":
            # SLA: 4h emergencial, 24h comum
            ttl_horas = 4 if solicitacao.classificacao == "Emergencial" else 24
            email = solicitacao.aprovador_n1_email
            nome = solicitacao.aprovador_n1_nome
        else:  # N2
            ttl_horas = 8  # SLA N2 = 8h
            email = solicitacao.aprovador_n2_email
            nome = solicitacao.aprovador_n2_nome

        # ── QA override: redireciona TODOS os tokens para o testador ─────────
        if settings.QA_APROVADOR_EMAIL:
            logger.warning("[QA] Token %s-%s redirecionado: %s → %s", solicitacao.protocolo, nivel, email, settings.QA_APROVADOR_EMAIL)
            email = settings.QA_APROVADOR_EMAIL
        # ─────────────────────────────────────────────────────────────────────

        token = TokenAprovacaoModel(
            uuid=str(uuid.uuid4()),
            solicitacao_id=solicitacao.id,
            nivel=nivel,
            email_aprovador=email,
            nome_aprovador=nome,
            status="PENDENTE",
            data_expiracao=datetime.now() + timedelta(hours=ttl_horas),
        )
        self.db.add(token)
        self.db.flush()  # preenche o id sem commit definitivo
        return token

    def _aprovador_esta_de_ferias(self, email: str) -> bool:
        """
        Consulta o BigQuery para verificar se o colaborador está com SITUACAO = 'Férias'.
        Em caso de falha na consulta, retorna False (fail-safe: não bloqueia o fluxo).
        """
        try:
            situacao = _bq_service.buscar_situacao_por_email(email)
            return situacao is not None and situacao.strip().lower() in _SITUACOES_FERIAS
        except Exception as e:
            logger.error(
                f"Erro ao verificar férias para '{email}' no BQ: {e}. "
                "Prosseguindo com aprovação N1 por segurança."
            )
            return False

    def _enviar_email_setor(self, solicitacao: SolicitacaoModel) -> None:
        try:
            from app.infrastructure.email_service import EmailService
            EmailService().enviar_email_setor_pendente(solicitacao)
        except Exception as e:
            logger.error(f"Falha ao enviar e-mail de pré-aprovação ao setor: {e}")

    def _enviar_email_aprovacao(self, solicitacao: SolicitacaoModel, token: TokenAprovacaoModel) -> None:
        try:
            from app.infrastructure.email_service import EmailService
            EmailService().enviar_email_aprovacao(solicitacao, token)
        except Exception as e:
            logger.error(f"Falha ao enviar e-mail de aprovação N{token.nivel}: {e}")

    def _enviar_email_resultado(
        self, solicitacao: SolicitacaoModel, nivel: str, acao: str, aprovador_nome: str
    ) -> None:
        try:
            from app.infrastructure.email_service import EmailService
            EmailService().enviar_email_resultado(solicitacao, nivel, acao, aprovador_nome)
        except Exception as e:
            logger.error(f"Falha ao enviar e-mail de resultado ao solicitante: {e}")
