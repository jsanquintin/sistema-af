"""Gestion de usuarios -- hoy solo lo minimo para que un admin pueda
restablecer la contrasena de otro usuario (ver
docs/designs/nucleo-contabilidad-nomina.md-adyacente: el proyecto no
tiene proveedor de email configurado, asi que la recuperacion
self-service por correo queda diferida; esto cubre el interin sin
bloquear al usuario que perdio su contrasena).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_db
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.schemas.usuario import RestablecerPasswordRequest, UsuarioResponse

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def _verificar_admin(usuario: Usuario) -> None:
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Solo un administrador puede hacer esto"
        )


@router.get("", response_model=list[UsuarioResponse])
def listar_usuarios(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[Usuario]:
    _verificar_admin(usuario)
    # RLS ya limita al tenant -- un admin ve todos los usuarios de su
    # propio tenant, nunca de otro.
    return list(db.execute(select(Usuario).order_by(Usuario.email)).scalars().all())


@router.post("/{usuario_id}/restablecer-password", status_code=status.HTTP_204_NO_CONTENT)
def restablecer_password(
    usuario_id: str,
    payload: RestablecerPasswordRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> None:
    _verificar_admin(usuario)
    objetivo = db.get(Usuario, usuario_id)
    if objetivo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    objetivo.hash_password = hash_password(payload.nueva_password)
    db.commit()
