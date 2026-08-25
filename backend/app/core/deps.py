from collections.abc import Generator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.usuario import Usuario

_bearer_scheme = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise unauthorized

    tenant_id = payload.get("tenant_id")
    usuario_id = payload.get("sub")
    if not tenant_id or not usuario_id:
        # Fail-closed: nunca continuar sin un tenant_id valido en el token.
        raise unauthorized

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo or str(usuario.tenant_id) != tenant_id:
        raise unauthorized

    return usuario
