from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except VerifyMismatchError:
        return False


def create_access_token(
    *, usuario_id: UUID, tenant_id: UUID, rol: str, impersonated_by: UUID | None = None
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "tenant_id": str(tenant_id),
        "rol": rol,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    if impersonated_by is not None:
        # Sesion de soporte: el resto del sistema ignora este claim (el
        # token sigue siendo un JWT de tenant normal), solo lo lee el
        # frontend para mostrar el aviso de "actuando como" y el log de
        # auditoria al emitirlo (ver app/api/superadmin.py).
        payload["impersonated_by"] = str(impersonated_by)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_superadmin_token(*, superadmin_id: UUID) -> str:
    # Sin tenant_id a proposito: get_current_user exige tenant_id y falla
    # cerrado si falta, asi que este token nunca puede usarse contra un
    # endpoint tenant-scoped (ver app/core/deps.py::get_current_user).
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(superadmin_id),
        "kind": "superadmin",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
