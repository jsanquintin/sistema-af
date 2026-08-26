from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_db
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteCreate, ClienteResponse

router = APIRouter(prefix="/clientes", tags=["clientes"])


def _verificar_acceso_empresa(usuario: Usuario, empresa_id: int) -> None:
    if usuario.empresa_id is not None and usuario.empresa_id != empresa_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a esta empresa")


@router.get("", response_model=list[ClienteResponse])
def listar_clientes(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[Cliente]:
    query = select(Cliente)
    if usuario.empresa_id is not None:
        query = query.where(Cliente.empresa_id == usuario.empresa_id)
    return list(db.execute(query).scalars().all())


@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(
    payload: ClienteCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> Cliente:
    _verificar_acceso_empresa(usuario, payload.empresa_id)
    cliente = Cliente(**payload.model_dump(), tenant_id=usuario.tenant_id)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(
    cliente_id: int,
    payload: ClienteCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> Cliente:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    _verificar_acceso_empresa(usuario, cliente.empresa_id)
    _verificar_acceso_empresa(usuario, payload.empresa_id)

    for campo, valor in payload.model_dump().items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(
    cliente_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> None:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    _verificar_acceso_empresa(usuario, cliente.empresa_id)

    # Borrado real -- clientes no tiene columna activo (a diferencia de
    # empleados/almacenes). Si en el futuro tiene facturas asociadas, la FK
    # rechaza el borrado en vez de dejar una factura huerfana.
    db.delete(cliente)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar: el cliente tiene registros asociados (ej. facturas)",
        )
