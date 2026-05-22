from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.infrastructure.orm.models import CotacaoModel, SolicitacaoModel
from app.domain.models.schemas import CotacaoCreate


class CotacaoService:

    def registrar_cotacao(
        self,
        db: Session,
        solicitacao_id: int,
        dados: CotacaoCreate,
        agencia_usuario: str,
        agencia_nome: str
    ) -> CotacaoModel:
        """Registra ou atualiza a cotação de uma solicitação."""
        solicitacao = db.query(SolicitacaoModel).filter(
            SolicitacaoModel.id == solicitacao_id
        ).first()

        if not solicitacao:
            raise ValueError(f"Solicitação {solicitacao_id} não encontrada.")

        if solicitacao.status not in ("AGUARDANDO_COTACAO", "COTACAO_ENVIADA", "PENDENTE_APROVACAO_SETOR_COTACAO"):
            raise ValueError(
                f"Solicitação no status '{solicitacao.status}' não aceita cotação."
            )

        # Upsert por (solicitacao_id, agencia_nome) — cada agência cota independentemente
        cotacao = db.query(CotacaoModel).filter(
            CotacaoModel.solicitacao_id == solicitacao_id,
            CotacaoModel.agencia_nome == agencia_nome
        ).first()

        if not cotacao:
            cotacao = CotacaoModel(solicitacao_id=solicitacao_id)
            db.add(cotacao)

        cotacao.agencia_nome    = agencia_nome
        cotacao.agencia_usuario = agencia_usuario
        cotacao.aereo_companhia    = dados.aereo_companhia
        cotacao.aereo_numero_voo   = dados.aereo_numero_voo
        cotacao.aereo_horario_ida  = dados.aereo_horario_ida
        cotacao.aereo_horario_volta = dados.aereo_horario_volta
        cotacao.aereo_valor        = dados.aereo_valor
        cotacao.hotel_nome         = dados.hotel_nome
        cotacao.hotel_categoria    = dados.hotel_categoria
        cotacao.hotel_valor_diaria = dados.hotel_valor_diaria
        cotacao.rodov_empresa      = dados.rodov_empresa
        cotacao.rodov_horario_ida  = dados.rodov_horario_ida
        cotacao.rodov_horario_volta = dados.rodov_horario_volta
        cotacao.rodov_valor        = dados.rodov_valor
        cotacao.carro_locadora     = dados.carro_locadora
        cotacao.carro_modelo       = dados.carro_modelo
        cotacao.carro_valor_diaria = dados.carro_valor_diaria
        cotacao.valor_total        = dados.valor_total
        cotacao.observacoes        = dados.observacoes
        cotacao.status             = "PENDENTE"

        # Avança o status da solicitação
        cotacoes_existentes = db.query(CotacaoModel).filter(
            CotacaoModel.solicitacao_id == solicitacao_id
        ).count()
        # Quando as duas agências (Tastur + Kontrip) já cotaram → aguarda decisão do Setor
        if cotacoes_existentes >= 2:
            solicitacao.status = "PENDENTE_APROVACAO_SETOR_COTACAO"
            try:
                from app.infrastructure.email_service import EmailService
                cotacoes = db.query(CotacaoModel).filter(
                    CotacaoModel.solicitacao_id == solicitacao_id
                ).all()
                EmailService().enviar_email_setor_comparativo(solicitacao, cotacoes)
            except Exception as e:
                logging.warning(f"Falha ao notificar setor para comparativo de cotações: {e}")
        else:
            solicitacao.status = "COTACAO_ENVIADA"

        db.commit()
        db.refresh(cotacao)
        logging.info(f"Cotação registrada para solicitação {solicitacao_id} por {agencia_usuario}.")

        # Notifica solicitante
        try:
            from app.infrastructure.email_service import EmailService
            EmailService().enviar_email_cotacao_recebida(solicitacao, cotacao)
        except Exception as e:
            logging.warning(f"Falha ao enviar e-mail de cotação recebida: {e}")

        return cotacao

    def listar_solicitacoes_agencia(self, db: Session, status_filtro: Optional[str] = None):
        """Lista solicitações visíveis para a agência (aprovadas ou com cotação)."""
        statuses_visiveis = ["AGUARDANDO_COTACAO", "COTACAO_ENVIADA", "PENDENTE_APROVACAO_SETOR_COTACAO", "APROVADA_AGUARDANDO_VOUCHER", "CONCLUIDA"]
        query = db.query(SolicitacaoModel).filter(
            SolicitacaoModel.status.in_(statuses_visiveis)
        )
        if status_filtro:
            query = query.filter(SolicitacaoModel.status == status_filtro)
        return query.order_by(SolicitacaoModel.data_criacao.desc()).all()

    def get_solicitacao_com_cotacao(self, db: Session, solicitacao_id: int):
        """Retorna a solicitação com a cotação associada (se houver)."""
        sol = db.query(SolicitacaoModel).filter(
            SolicitacaoModel.id == solicitacao_id
        ).first()
        if not sol:
            return None, None
        cotacao = db.query(CotacaoModel).filter(
            CotacaoModel.solicitacao_id == solicitacao_id
        ).first()
        return sol, cotacao
