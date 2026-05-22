from sqlalchemy.orm import Session
from app.repositories.viagens_repository import ViagensRepository
from app.infrastructure.orm import models as orm_models
from app.domain.models import schemas
from datetime import datetime, timedelta

class ViagensService:
    def __init__(self, db: Session):
        self.repo = ViagensRepository(db)

    def create_nova_solicitacao(self, solicitacao_data: schemas.SolicitacaoCreate, username: str) -> orm_models.SolicitacaoModel:
        """Aplica as regras de neg?cio e cria uma nova solicita??o."""
        
        # O Pydantic nos entrega a data_ida da Web (pode vir com fuso hor?rio)
        # Vamos remover o fuso (torn?-la naive) para evitar erro de compara??o no Python
        data_ida_limpa = solicitacao_data.data_ida.replace(tzinfo=None)
        
        # Pegamos a data atual tamb?m limpa (naive) e somamos 15 dias
        data_limite_diretoria = datetime.now().replace(tzinfo=None) + timedelta(days=15)

        # REGRA DE NEG?CIO: Viagens com menos de 15 dias de anteced?ncia exigem diretoria
        exige_diretoria = False
        if data_ida_limpa < data_limite_diretoria:
            exige_diretoria = True

        # Converte o schema Pydantic para o modelo do banco de dados
        solicitacao_orm = orm_models.SolicitacaoModel(
            solicitante_username=username,
            destino=solicitacao_data.destino,
            data_ida=data_ida_limpa,  # Salvamos a data limpa
            data_volta=solicitacao_data.data_volta.replace(tzinfo=None) if solicitacao_data.data_volta else None,
            motivo=solicitacao_data.motivo,
            condicao_especial=solicitacao_data.condicao_especial,
            exige_aprovacao_diretoria=exige_diretoria,
            status="AGUARDANDO_DIRETORIA" if exige_diretoria else "AGUARDANDO_N1"
        )

        return self.repo.create_solicitacao(solicitacao_orm)
