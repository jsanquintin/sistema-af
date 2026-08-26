from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.acceso import empresa_de_sucursal, sucursales_de_empresa, verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.lote_cosecha import LoteCosecha
from app.models.usuario import Usuario
from app.schemas.lote_cosecha import LoteCosechaCreate, LoteCosechaResponse

router = APIRouter(prefix="/lotes-cosecha", tags=["lotes-cosecha"])


@router.get("", response_model=list[LoteCosechaResponse])
def listar_lotes(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[LoteCosecha]:
    verificar_acceso_empresa(usuario, empresa_id)
    query = select(LoteCosecha).where(LoteCosecha.sucursal_id.in_(sucursales_de_empresa(empresa_id)))
    return list(db.execute(query).scalars().all())


@router.post("", response_model=LoteCosechaResponse, status_code=status.HTTP_201_CREATED)
def crear_lote(
    payload: LoteCosechaCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> LoteCosecha:
    verificar_acceso_empresa(usuario, empresa_de_sucursal(db, payload.sucursal_id))
    lote = LoteCosecha(**payload.model_dump(), tenant_id=usuario.tenant_id, estado="disponible", costo_acumulado=0)
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return lote


@router.put("/{lote_id}", response_model=LoteCosechaResponse)
def actualizar_lote(
    lote_id: int,
    payload: LoteCosechaCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> LoteCosecha:
    lote = db.get(LoteCosecha, lote_id)
    if lote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")
    verificar_acceso_empresa(usuario, empresa_de_sucursal(db, lote.sucursal_id))
    verificar_acceso_empresa(usuario, empresa_de_sucursal(db, payload.sucursal_id))
    # cantidad/costo_acumulado/estado los mueve la bitacora de movimientos,
    # no este PUT -- solo los campos descriptivos del lote son editables aqui.
    for campo, valor in payload.model_dump().items():
        setattr(lote, campo, valor)
    db.commit()
    db.refresh(lote)
    return lote


@router.delete("/{lote_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_lote(
    lote_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> None:
    lote = db.get(LoteCosecha, lote_id)
    if lote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")
    verificar_acceso_empresa(usuario, empresa_de_sucursal(db, lote.sucursal_id))
    db.delete(lote)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar: el lote ya tiene movimientos de inventario registrados",
        )
