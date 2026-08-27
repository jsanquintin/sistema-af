from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import create_access_token, create_superadmin_token, verify_password
from app.models.superadmin import Superadmin
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Email o password incorrectos",
)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    # email es unico por (tenant_id, email), no globalmente. Con un solo
    # tenant activo esto no es ambiguo; si aparece mas de un tenant, esta
    # busqueda deja de ser suficiente y hay que resolver primero a que
    # tenant pertenece el usuario (paso de login separado, no implementado).
    usuarios = db.execute(
        select(Usuario).where(Usuario.email == payload.email, Usuario.activo.is_(True))
    ).scalars().all()

    if len(usuarios) == 1:
        usuario = usuarios[0]
        if verify_password(payload.password, usuario.hash_password):
            token = create_access_token(usuario_id=usuario.id, tenant_id=usuario.tenant_id, rol=usuario.rol)
            return TokenResponse(access_token=token)
        raise _INVALID_CREDENTIALS

    if len(usuarios) == 0:
        # Sin usuario de tenant con ese email: puede ser un superadmin.
        # Un solo formulario de login para ambos -- ver
        # docs/designs/panel-superadmin-multitenant.md. Deliberadamente NO
        # se intenta esto cuando ya hubo un match de tenant (len == 1) con
        # password incorrecto, para no crear un segundo intento de match
        # sobre la misma credencial.
        superadmin = db.execute(
            select(Superadmin).where(Superadmin.email == payload.email, Superadmin.activo.is_(True))
        ).scalar_one_or_none()
        if superadmin is not None and verify_password(payload.password, superadmin.hash_password):
            token = create_superadmin_token(superadmin_id=superadmin.id)
            return TokenResponse(access_token=token)

    raise _INVALID_CREDENTIALS


@router.get("/me")
def me(usuario: Usuario = Depends(get_current_user)) -> dict:
    return {
        "id": str(usuario.id),
        "email": usuario.email,
        "nombre_completo": usuario.nombre_completo,
        "rol": usuario.rol,
        "tenant_id": str(usuario.tenant_id),
    }
