from collections.abc import Generator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import AppSessionLocal, SessionLocal
from app.models.superadmin import Superadmin
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


def get_tenant_db(usuario: Usuario = Depends(get_current_user)) -> Generator[Session, None, None]:
    """Sesion de negocio, con RLS forzado por app_user.

    Fail-closed por construccion: fija app.tenant_id ANTES de devolver la
    sesion, usando el tenant_id ya validado en el JWT (get_current_user).
    Sin este SET, las politicas RLS con FORCE ROW LEVEL SECURITY hacen
    current_setting('app.tenant_id') fallar -- cero filas visibles, nunca
    un tenant por defecto.
    """
    db = AppSessionLocal()
    try:
        db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id": str(usuario.tenant_id)})
        yield db
    finally:
        db.close()


def get_superadmin_db() -> Generator[Session, None, None]:
    """Sesion para el panel de superadmin.

    Corre como app_user (igual que get_tenant_db), pero SIN fijar
    app.tenant_id de entrada: `superadmins`, `superadmin_auditoria` y
    `tenants` no tienen RLS (ver docs/designs/panel-superadmin-multitenant.md),
    asi que no hace falta el rol con BYPASSRLS que se habia anticipado en
    CONTEXTO.md. Los endpoints que necesitan leer/escribir usuarios de un
    tenant especifico (alta del primer admin, elegir a quien impersonar)
    fijan app.tenant_id ellos mismos, una vez que ya saben a que tenant
    apuntan -- nunca antes.
    """
    db = AppSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_superadmin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_superadmin_db),
) -> Superadmin:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise unauthorized

    if payload.get("kind") != "superadmin":
        # Fail-closed: un JWT de tenant normal (o cualquier otro shape)
        # nunca debe pasar por aca, aunque este bien firmado.
        raise unauthorized

    superadmin_id = payload.get("sub")
    if not superadmin_id:
        raise unauthorized

    superadmin = db.get(Superadmin, superadmin_id)
    if superadmin is None or not superadmin.activo:
        raise unauthorized

    return superadmin
