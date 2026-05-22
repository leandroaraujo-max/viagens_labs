from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.infrastructure.database import SessionLocal
from app.core.security import SECRET_KEY, ALGORITHM

_security_bearer = HTTPBearer(auto_error=False)


def get_db_session():
    """Cria e fornece uma sessão do banco de dados por requisição."""
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db:
            db.close()


def _decode_payload(credentials: HTTPAuthorizationCredentials) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente.",
        )
    try:
        return jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )


def get_current_username(
    credentials: HTTPAuthorizationCredentials = Depends(_security_bearer),
) -> str:
    """Extrai e valida o username do JWT."""
    payload = _decode_payload(credentials)
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")
    return username


def get_current_perfil(
    credentials: HTTPAuthorizationCredentials = Depends(_security_bearer),
) -> tuple[str, str]:
    """Retorna (username, perfil) do JWT. Útil para endpoints que precisam do perfil."""
    payload = _decode_payload(credentials)
    username: str = payload.get("sub", "")
    perfil: str = payload.get("perfil", "")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")
    return username, perfil


def require_agencia(
    credentials: HTTPAuthorizationCredentials = Depends(_security_bearer),
) -> tuple[str, str]:
    """
    Garante que o token pertence a um usuário com perfil 'agencia'.
    Retorna (username, agencia_nome).
    """
    payload = _decode_payload(credentials)
    perfil: str = payload.get("perfil", "")
    if perfil != "agencia":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao portal da agência.",
        )
    username: str = payload.get("sub", "")
    agencia_nome: str = payload.get("agencia_nome", "")
    return username, agencia_nome


def require_setor(
    credentials: HTTPAuthorizationCredentials = Depends(_security_bearer),
) -> str:
    """
    Garante que o token pertence a um usuário com perfil 'setor'.
    Retorna o username do colaborador.
    """
    payload = _decode_payload(credentials)
    perfil: str = payload.get("perfil", "")
    if perfil != "setor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao portal do setor.",
        )
    return payload.get("sub", "")


def get_optional_username(
    credentials: HTTPAuthorizationCredentials = Depends(_security_bearer),
) -> str | None:
    """Retorna o username do JWT se válido, None caso contrário."""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
