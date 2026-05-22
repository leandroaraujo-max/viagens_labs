from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# --- SCHEMAS DE VIAGENS ---

class SolicitacaoCreate(BaseModel):
    """Schema para valida??o de entrada (quando o colaborador cria a viagem)"""
    destino: str
    data_ida: datetime
    data_volta: Optional[datetime] = None
    motivo: str
    condicao_especial: bool = False

class SolicitacaoResponse(BaseModel):
    """Schema para sa?da de dados (o que a API devolve para o front)"""
    id: int
    solicitante_username: str
    destino: str
    status: str
    data_criacao: datetime

    model_config = ConfigDict(from_attributes=True)

# --- SCHEMAS DE AUTENTICA??O ---

class LoginCredentials(BaseModel):
    """Schema para receber o usu?rio e a senha da requisi??o de login."""
    username: str
    password: str
    agencia: Optional[str] = None

class TokenResponse(BaseModel):
    """Schema para a devolu??o do Token JWT gerado."""
    access_token: str
    token_type: str = "bearer"
    nome_usuario: str
    perfil: str
