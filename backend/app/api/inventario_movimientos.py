from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.acceso import empresa_de_lote, sucursales_de_empresa, verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.inventario_movimiento import InventarioMovimiento
from app.models.lote_cosecha import LoteCosecha
from app.models.usuario import Usuario
from app.schemas.inventario_movimiento import InventarioMovimientoCreate, InventarioMovimientoResponse

router = APIRouter(prefix="/inventario-movimientos", tags=["inventario-movimientos"])


def _lotes_de_empresa(empresa_id: int):
    return select(LoteCosecha.id).where(LoteCosecha.sucursal_id.in_(sucursales_de_empresa(empresa_id)))


@router.get("", response_model=list[InventarioMovimientoResponse])
def listar_movimientos(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[InventarioMovimiento]:
    verificar_acceso_empresa(usuario, empresa_id)
    query = (
        select(InventarioMovimiento)
        .where(InventarioMovimiento.lote_id.in_(_lotes_de_empresa(empresa_id)))
        .order_by(InventarioMovimiento.fecha.desc())
    )
    return list(db.execute(query).scalars().all())


@router.post("", response_model=InventarioMovimientoResponse, status_code=status.HTTP_201_CREATED)
def crear_movimiento(
    payload: InventarioMovimientoCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> InventarioMovimiento:
    verificar_acceso_empresa(usuario, empresa_de_lote(db, payload.lote_id))
    # Sin UPDATE ni DELETE a proposito: es una bitacora, igual que un
    # asiento contable -- un error se corrige con un movimiento contrario,
    # no editando ni borrando el historial.
    movimiento = InventarioMovimiento(**payload.model_dump(), tenant_id=usuario.tenant_id)
    db.add(movimiento)
    db.commit()
    db.refresh(movimiento)
    return movimiento
