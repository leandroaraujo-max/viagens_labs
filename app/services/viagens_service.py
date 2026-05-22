from sqlalchemy.orm import Session
from app.repositories.viagens_repository import ViagensRepository
from app.infrastructure.orm import models as orm_models
from app.domain.models import schemas
from datetime import datetime


class ViagensService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ViagensRepository(db)

    def _gerar_protocolo(self) -> str:
        """Gera protocolo único no formato REQ-YYYY-NNN."""
        ano = datetime.now().year
        total = self.db.query(orm_models.SolicitacaoModel).filter(
            orm_models.SolicitacaoModel.protocolo.like(f"REQ-{ano}-%")
        ).count()
        return f"REQ-{ano}-{str(total + 1).zfill(3)}"

    def create_nova_solicitacao(
        self, solicitacao_data: schemas.SolicitacaoCreate, username: str
    ) -> orm_models.SolicitacaoModel:
        """Aplica as regras de negócio e persiste a solicitação completa."""

        data_ida = solicitacao_data.data_ida.replace(tzinfo=None)
        agora = datetime.now()
        antecedencia_dias = (data_ida - agora).days

        # REGRA DE NEGÓCIO: aéreo com < 15 dias = Emergencial → exige N1 + N2
        servicos = solicitacao_data.tipo_servico
        tem_aereo = 'Aereo' in servicos
        classificacao = 'Emergencial' if (tem_aereo and antecedencia_dias < 15) else 'Comum'
        exige_diretoria = classificacao == 'Emergencial'
        status_inicial = 'AGUARDANDO_DIRETORIA' if exige_diretoria else 'AGUARDANDO_N1'

        protocolo = self._gerar_protocolo()

        solicitacao_orm = orm_models.SolicitacaoModel(
            protocolo=protocolo,
            solicitante_username=username,
            via_delegacao=solicitacao_data.via_delegacao,
            # Passo 2
            origem_cidade=solicitacao_data.origem_cidade,
            origem_estado=solicitacao_data.origem_estado,
            destino_cidade=solicitacao_data.destino_cidade,
            destino_estado=solicitacao_data.destino_estado,
            data_ida=data_ida,
            data_volta=solicitacao_data.data_volta.replace(tzinfo=None) if solicitacao_data.data_volta else None,
            motivo_viagem=solicitacao_data.motivo_viagem,
            tipo_servico=','.join(servicos),
            antecedencia_dias=antecedencia_dias,
            classificacao=classificacao,
            exige_aprovacao_diretoria=exige_diretoria,
            # Passo 3 - Aéreo
            aereo_periodo_preferido=solicitacao_data.aereo_periodo_preferido,
            aereo_tipo_trecho=solicitacao_data.aereo_tipo_trecho,
            bagagem_extra=solicitacao_data.bagagem_extra,
            assento_especial=solicitacao_data.assento_especial,
            # Passo 3 - Rodoviário
            rodov_periodo_preferido=solicitacao_data.rodov_periodo_preferido,
            rodov_tipo_onibus=solicitacao_data.rodov_tipo_onibus,
            rodov_tipo_trecho=solicitacao_data.rodov_tipo_trecho,
            # Passo 3 - Hospedagem
            preferencia_hotel_nome=solicitacao_data.preferencia_hotel_nome,
            quarto_excecao_saude=solicitacao_data.quarto_excecao_saude,
            # Passo 3 - Carro
            carro_data_retirada=solicitacao_data.carro_data_retirada,
            carro_hora_retirada=solicitacao_data.carro_hora_retirada,
            carro_cidade_retirada=solicitacao_data.carro_cidade_retirada,
            carro_data_devolucao=solicitacao_data.carro_data_devolucao,
            carro_hora_devolucao=solicitacao_data.carro_hora_devolucao,
            carro_cidade_devolucao=solicitacao_data.carro_cidade_devolucao,
            # Obs
            observacoes_viajante=solicitacao_data.observacoes_viajante,
            preferencia_voo=solicitacao_data.preferencia_voo,
            preferencia_voo_volta=solicitacao_data.preferencia_voo_volta,
            # Cadeia de aprovação
            aprovador_n1_email=solicitacao_data.aprovador_n1_email,
            aprovador_n1_nome=solicitacao_data.aprovador_n1_nome,
            aprovador_n2_email=solicitacao_data.aprovador_n2_email,
            aprovador_n2_nome=solicitacao_data.aprovador_n2_nome,
            # Perfil do viajante
            viajante_nome=solicitacao_data.viajante_nome,
            viajante_cpf=solicitacao_data.viajante_cpf,
            viajante_matricula=solicitacao_data.viajante_matricula,
            viajante_email=solicitacao_data.viajante_email,
            viajante_cargo=solicitacao_data.viajante_cargo,
            viajante_filial=solicitacao_data.viajante_filial,
            viajante_centro_custo=solicitacao_data.viajante_centro_custo,
            viajante_cod_centro_custo=solicitacao_data.viajante_cod_centro_custo,
            viajante_data_admissao=solicitacao_data.viajante_data_admissao,
            viajante_celular=solicitacao_data.viajante_celular,
            viajante_data_nascimento=solicitacao_data.viajante_data_nascimento,
            status=status_inicial,
        )

        solicitacao_salva = self.repo.create_solicitacao(solicitacao_orm)

        # Dispara fluxo de aprovação (gera token N1 e envia e-mail)
        try:
            from app.services.aprovacao_service import AprovacaoService
            AprovacaoService(self.db).iniciar_fluxo_aprovacao(solicitacao_salva)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erro ao iniciar aprovação: {e}")

        # Confirma criação por e-mail ao solicitante
        try:
            from app.infrastructure.email_service import EmailService
            EmailService().enviar_email_criacao(solicitacao_salva)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Falha ao enviar e-mail de confirmação: {e}")

        return solicitacao_salva
