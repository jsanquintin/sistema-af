from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.acceso import verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.regla_contabilizacion import ReglaContabilizacion
from app.models.usuario import Usuario
from app.schemas.regla_contabilizacion import ReglaContabilizacionCreate, ReglaContabilizacionResponse

router = APIRouter(prefix="/reglas-contabilizacion", tags=["reglas-contabilizacion"])


@router.get("", response_model=list[ReglaContabilizacionResponse])
def listar_reglas(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[ReglaContabilizacion]:
    verificar_acceso_empresa(usuario, empresa_id)
    query = select(ReglaContabilizacion).where(ReglaContabilizacion.empresa_id == empresa_id)
    return list(db.execute(query).scalars().all())


@router.post("", response_model=ReglaContabilizacionResponse, status_code=status.HTTP_201_CREATED)
def crear_regla(
    payload: ReglaContabilizacionCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> ReglaContabilizacion:
    verificar_acceso_empresa(usuario, payload.empresa_id)
    regla = ReglaContabilizacion(**payload.model_dump(), tenant_id=usuario.tenant_id)
    db.add(regla)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una regla para esta empresa/origen/evento/cuenta, o la cuenta no existe en el catalogo",
        )
    db.refresh(regla)
    return regla


@router.put("/{regla_id}", response_model=ReglaContabilizacionResponse)
def actualizar_regla(
    regla_id: int,
    payload: ReglaContabilizacionCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> ReglaContabilizacion:
    regla = db.get(ReglaContabilizacion, regla_id)
    if regla is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla no encontrada")
    verificar_acceso_empresa(usuario, regla.empresa_id)
    verificar_acceso_empresa(usuario, payload.empresa_id)

    for campo, valor in payload.model_dump().items():
        setattr(regla, campo, valor)
    db.commit()
    db.refresh(regla)
    return regla


@router.delete("/{regla_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_regla(
    regla_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> None:
    regla = db.get(ReglaContabilizacion, regla_id)
    if regla is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla no encontrada")
    verificar_acceso_empresa(usuario, regla.empresa_id)
    db.delete(regla)
    db.commit()
