from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_db
from app.models.inventario_movimiento import InventarioMovimiento
from app.models.usuario import Usuario
from app.schemas.inventario_movimiento import InventarioMovimientoCreate, InventarioMovimientoResponse

router = APIRouter(prefix="/inventario-movimientos", tags=["inventario-movimientos"])


@router.get("", response_model=list[InventarioMovimientoResponse])
def listar_movimientos(db: Session = Depends(get_tenant_db)) -> list[InventarioMovimiento]:
    return list(
        db.execute(select(InventarioMovimiento).order_by(InventarioMovimiento.fecha.desc())).scalars().all()
    )


@router.post("", response_model=InventarioMovimientoResponse, status_code=status.HTTP_201_CREATED)
def crear_movimiento(
    payload: InventarioMovimientoCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> InventarioMovimiento:
    # Sin UPDATE ni DELETE a proposito: es una bitacora, igual que un
    # asiento contable -- un error se corrige con un movimiento contrario,
    # no editando ni borrando el historial.
    movimiento = InventarioMovimiento(**payload.model_dump(), tenant_id=usuario.tenant_id)
    db.add(movimiento)
    db.commit()
    db.refresh(movimiento)
    return movimiento
