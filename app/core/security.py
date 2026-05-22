from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
from jose import jwt
from passlib.context import CryptContext

# Configura??o JWT
# TODO: Em produ??o, mover essa SECRET_KEY para as vari?veis de ambiente (.env)
SECRET_KEY = "magalu_gfl_viagens_super_secret_key_remover_em_prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

# Configura o Passlib para usar Bcrypt (o padr?o ouro de mercado, muito mais seguro que SHA-256 + Salt manual)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    perfil: str = "viajante",
    extra_claims: Optional[dict] = None
) -> str:
    """
    Cria um JSON Web Token (JWT) assinado digitalmente.
    extra_claims: campos adicionais opcionais (ex: {'agencia_nome': 'Tastur'}).
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode: dict = {"exp": expire, "sub": str(subject), "perfil": perfil}
    if extra_claims:
        to_encode.update(extra_claims)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto plano bate com o hash bcrypt (Usado para Ag?ncias)"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera o hash bcrypt (o Bcrypt j? gera e gerencia o Salt automaticamente por baixo dos panos)"""
    return pwd_context.hash(password)
