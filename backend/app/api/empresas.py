from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_db
from app.models.empresa import Empresa
from app.models.sucursal import Sucursal
from app.models.usuario import Usuario
from app.schemas.empresa import EmpresaResponse, SucursalResponse

router = APIRouter(prefix="/empresas", tags=["empresas"])


@router.get("", response_model=list[EmpresaResponse])
def listar_empresas(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[Empresa]:
    # RLS ya limita al tenant. Ademas de eso, si el usuario tiene empresa_id
    # fijo (no NULL) solo puede ver esa empresa, nunca las demas del tenant.
    query = select(Empresa).where(Empresa.activo.is_(True))
    if usuario.empresa_id is not None:
        query = query.where(Empresa.id == usuario.empresa_id)
    return list(db.execute(query).scalars().all())


@router.get("/{empresa_id}/sucursales", response_model=list[SucursalResponse])
def listar_sucursales(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[Sucursal]:
    if usuario.empresa_id is not None and usuario.empresa_id != empresa_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a esta empresa")

    return list(
        db.execute(
            select(Sucursal).where(Sucursal.empresa_id == empresa_id, Sucursal.activo.is_(True))
        )
        .scalars()
        .all()
    )
