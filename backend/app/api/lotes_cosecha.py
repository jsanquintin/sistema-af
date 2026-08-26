from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_db
from app.models.lote_cosecha import LoteCosecha
from app.models.usuario import Usuario
from app.schemas.lote_cosecha import LoteCosechaCreate, LoteCosechaResponse

router = APIRouter(prefix="/lotes-cosecha", tags=["lotes-cosecha"])


@router.get("", response_model=list[LoteCosechaResponse])
def listar_lotes(db: Session = Depends(get_tenant_db)) -> list[LoteCosecha]:
    return list(db.execute(select(LoteCosecha)).scalars().all())


@router.post("", response_model=LoteCosechaResponse, status_code=status.HTTP_201_CREATED)
def crear_lote(
    payload: LoteCosechaCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> LoteCosecha:
    lote = LoteCosecha(**payload.model_dump(), tenant_id=usuario.tenant_id, estado="disponible", costo_acumulado=0)
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return lote


@router.put("/{lote_id}", response_model=LoteCosechaResponse)
def actualizar_lote(lote_id: int, payload: LoteCosechaCreate, db: Session = Depends(get_tenant_db)) -> LoteCosecha:
    lote = db.get(LoteCosecha, lote_id)
    if lote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")
    # cantidad/costo_acumulado/estado los mueve la bitacora de movimientos,
    # no este PUT -- solo los campos descriptivos del lote son editables aqui.
    for campo, valor in payload.model_dump().items():
        setattr(lote, campo, valor)
    db.commit()
    db.refresh(lote)
    return lote


@router.delete("/{lote_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_lote(lote_id: int, db: Session = Depends(get_tenant_db)) -> None:
    lote = db.get(LoteCosecha, lote_id)
    if lote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")
    db.delete(lote)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar: el lote ya tiene movimientos de inventario registrados",
        )
