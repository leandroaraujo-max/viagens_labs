from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.infrastructure.database import Base

class SolicitacaoModel(Base):
    __tablename__ = "solicitacoes"

    id = Column(Integer, primary_key=True, index=True)
    
    # Referência ao AD (ex: leandro.araujo) - Não precisamos do nome completo, pegamos do BQ depois
    solicitante_username = Column(String(100), index=True, nullable=False)
    
    # Dados da Viagem
    destino = Column(String(200), nullable=False)
    data_ida = Column(DateTime, nullable=False)
    data_volta = Column(DateTime, nullable=True)
    motivo = Column(Text, nullable=False)
    
    # Flag importante da nossa regra de negócio: Necessita de voo ou < 15 dias (Diretoria)
    exige_aprovacao_diretoria = Column(Boolean, default=False)
    
    # PCD / Condição Especial (Sem upload obrigatório, conforme alinhamento com a Rubia)
    condicao_especial = Column(Boolean, default=False)
    
    # Status da solicitação (ex: AGUARDANDO_N1, AGUARDANDO_DIRETORIA, APROVADO, EM_COTACAO, FINALIZADO)
    status = Column(String(50), default="AGUARDANDO_N1")
    
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    data_atualizacao = Column(DateTime(timezone=True), onupdate=func.now())


class VoucherModel(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, index=True)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False)
    
    # Tipo de Voucher: VOO, HOSPEDAGEM, TRANSPORTE (Individualizados para a agência anexar separadamente)
    tipo_voucher = Column(String(50), nullable=False)
    
    # Caminho do arquivo físico no servidor Windows (ex: C:\inetpub\vouchers\doc.pdf) ou URL
    caminho_arquivo = Column(String(500), nullable=False)
    
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
