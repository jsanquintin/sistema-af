from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.acceso import verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.obra import Obra
from app.models.sucursal import Sucursal
from app.models.usuario import Usuario
from app.schemas.obra import ObraCreate, ObraResponse

router = APIRouter(prefix="/obras", tags=["obras"])


def _validar_sucursal_es_proyecto(db: Session, sucursal_id: int, empresa_id: int) -> None:
    sucursal = db.get(Sucursal, sucursal_id)
    if sucursal is None or sucursal.empresa_id != empresa_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sucursal invalida para esta empresa")
    if sucursal.tipo != "proyecto":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La sucursal debe ser de tipo 'proyecto' (es '{sucursal.tipo}')",
        )


@router.get("", response_model=list[ObraResponse])
def listar_obras(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[Obra]:
    verificar_acceso_empresa(usuario, empresa_id)
    return list(db.execute(select(Obra).where(Obra.empresa_id == empresa_id)).scalars().all())


@router.post("", response_model=ObraResponse, status_code=status.HTTP_201_CREATED)
def crear_obra(
    payload: ObraCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> Obra:
    verificar_acceso_empresa(usuario, payload.empresa_id)
    _validar_sucursal_es_proyecto(db, payload.sucursal_id, payload.empresa_id)
    obra = Obra(
        **payload.model_dump(),
        tenant_id=usuario.tenant_id,
        estado="en_proceso",
        costo_acumulado=0,
        costo_reconocido=0,
    )
    db.add(obra)
    db.commit()
    db.refresh(obra)
    return obra


@router.put("/{obra_id}", response_model=ObraResponse)
def actualizar_obra(
    obra_id: int,
    payload: ObraCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> Obra:
    obra = db.get(Obra, obra_id)
    if obra is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada")
    verificar_acceso_empresa(usuario, obra.empresa_id)
    verificar_acceso_empresa(usuario, payload.empresa_id)
    _validar_sucursal_es_proyecto(db, payload.sucursal_id, payload.empresa_id)
    # costo_acumulado/costo_reconocido/estado los mueve el cierre de nomina
    # y la facturacion, no este PUT -- solo los campos del contrato son
    # editables aqui (mismo criterio que lotes_cosecha.py).
    for campo, valor in payload.model_dump().items():
        setattr(obra, campo, valor)
    db.commit()
    db.refresh(obra)
    return obra


@router.delete("/{obra_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_obra(
    obra_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> None:
    obra = db.get(Obra, obra_id)
    if obra is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada")
    verificar_acceso_empresa(usuario, obra.empresa_id)
    db.delete(obra)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar: la obra ya tiene facturas o nominas asociadas",
        )
