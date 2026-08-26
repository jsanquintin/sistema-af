from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.acceso import empresa_de_sucursal, sucursales_de_empresa, verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.almacen import Almacen
from app.models.usuario import Usuario
from app.schemas.almacen import AlmacenCreate, AlmacenResponse

router = APIRouter(prefix="/almacenes", tags=["almacenes"])


@router.get("", response_model=list[AlmacenResponse])
def listar_almacenes(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[Almacen]:
    verificar_acceso_empresa(usuario, empresa_id)
    query = select(Almacen).where(
        Almacen.activo.is_(True), Almacen.sucursal_id.in_(sucursales_de_empresa(empresa_id))
    )
    return list(db.execute(query).scalars().all())


@router.post("", response_model=AlmacenResponse, status_code=status.HTTP_201_CREATED)
def crear_almacen(
    payload: AlmacenCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> Almacen:
    verificar_acceso_empresa(usuario, empresa_de_sucursal(db, payload.sucursal_id))
    almacen = Almacen(**payload.model_dump(), tenant_id=usuario.tenant_id, activo=True)
    db.add(almacen)
    db.commit()
    db.refresh(almacen)
    return almacen


@router.put("/{almacen_id}", response_model=AlmacenResponse)
def actualizar_almacen(
    almacen_id: int,
    payload: AlmacenCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> Almacen:
    almacen = db.get(Almacen, almacen_id)
    if almacen is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Almacén no encontrado")
    verificar_acceso_empresa(usuario, empresa_de_sucursal(db, almacen.sucursal_id))
    verificar_acceso_empresa(usuario, empresa_de_sucursal(db, payload.sucursal_id))

    for campo, valor in payload.model_dump().items():
        setattr(almacen, campo, valor)
    db.commit()
    db.refresh(almacen)
    return almacen


@router.delete("/{almacen_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_almacen(
    almacen_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> None:
    almacen = db.get(Almacen, almacen_id)
    if almacen is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Almacén no encontrado")
    verificar_acceso_empresa(usuario, empresa_de_sucursal(db, almacen.sucursal_id))
    almacen.activo = False
    db.commit()
