from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.acceso import verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.empleado import Empleado
from app.models.usuario import Usuario
from app.schemas.empleado import EmpleadoCreate, EmpleadoResponse

router = APIRouter(prefix="/empleados", tags=["empleados"])


@router.get("", response_model=list[EmpleadoResponse])
def listar_empleados(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[Empleado]:
    verificar_acceso_empresa(usuario, empresa_id)
    query = select(Empleado).where(Empleado.activo.is_(True), Empleado.empresa_id == empresa_id)
    return list(db.execute(query).scalars().all())


@router.post("", response_model=EmpleadoResponse, status_code=status.HTTP_201_CREATED)
def crear_empleado(
    payload: EmpleadoCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> Empleado:
    verificar_acceso_empresa(usuario, payload.empresa_id)
    empleado = Empleado(**payload.model_dump(), tenant_id=usuario.tenant_id, activo=True)
    db.add(empleado)
    db.commit()
    db.refresh(empleado)
    return empleado


@router.put("/{empleado_id}", response_model=EmpleadoResponse)
def actualizar_empleado(
    empleado_id: int,
    payload: EmpleadoCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> Empleado:
    empleado = db.get(Empleado, empleado_id)
    if empleado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado")
    verificar_acceso_empresa(usuario, empleado.empresa_id)
    verificar_acceso_empresa(usuario, payload.empresa_id)

    for campo, valor in payload.model_dump().items():
        setattr(empleado, campo, valor)
    db.commit()
    db.refresh(empleado)
    return empleado


@router.delete("/{empleado_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_empleado(
    empleado_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> None:
    empleado = db.get(Empleado, empleado_id)
    if empleado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado")
    verificar_acceso_empresa(usuario, empleado.empresa_id)

    # Soft-delete (activo=false), no borrado real -- un empleado con
    # historial de nomina no puede desaparecer del registro.
    empleado.activo = False
    db.commit()
