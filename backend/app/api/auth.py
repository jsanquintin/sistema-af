from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import create_access_token, verify_password
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

    if len(usuarios) != 1:
        raise _INVALID_CREDENTIALS

    usuario = usuarios[0]
    if not verify_password(payload.password, usuario.hash_password):
        raise _INVALID_CREDENTIALS

    token = create_access_token(usuario_id=usuario.id, tenant_id=usuario.tenant_id, rol=usuario.rol)
    return TokenResponse(access_token=token)


@router.get("/me")
def me(usuario: Usuario = Depends(get_current_user)) -> dict:
    return {
        "id": str(usuario.id),
        "email": usuario.email,
        "nombre_completo": usuario.nombre_completo,
        "rol": usuario.rol,
        "tenant_id": str(usuario.tenant_id),
    }
