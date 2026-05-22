from sqlalchemy.orm import Session
from app.infrastructure.orm import models as orm_models
from app.domain.models import schemas

class ViagensRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_solicitacao(self, solicitacao_orm: orm_models.SolicitacaoModel) -> orm_models.SolicitacaoModel:
        """Salva uma nova solicita??o no banco de dados."""
        self.db.add(solicitacao_orm)
        self.db.commit()
        self.db.refresh(solicitacao_orm)
        return solicitacao_orm
