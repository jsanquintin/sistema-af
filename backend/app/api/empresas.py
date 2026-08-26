from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.acceso import verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.empresa import Empresa
from app.models.sucursal import Sucursal
from app.models.usuario import Usuario
from app.schemas.empresa import EmpresaResponse, EmpresaUpdate, SucursalCreate, SucursalResponse

router = APIRouter(prefix="/empresas", tags=["empresas"])


def _obtener_empresa_o_404(db: Session, empresa_id: int) -> Empresa:
    empresa = db.get(Empresa, empresa_id)
    if empresa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")
    return empresa


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


@router.put("/{empresa_id}", response_model=EmpresaResponse)
def actualizar_empresa(
    empresa_id: int,
    payload: EmpresaUpdate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> Empresa:
    verificar_acceso_empresa(usuario, empresa_id)
    empresa = _obtener_empresa_o_404(db, empresa_id)
    for campo, valor in payload.model_dump().items():
        setattr(empresa, campo, valor)
    db.commit()
    db.refresh(empresa)
    return empresa


@router.get("/{empresa_id}/sucursales", response_model=list[SucursalResponse])
def listar_sucursales(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[Sucursal]:
    verificar_acceso_empresa(usuario, empresa_id)
    return list(
        db.execute(
            select(Sucursal).where(Sucursal.empresa_id == empresa_id, Sucursal.activo.is_(True))
        )
        .scalars()
        .all()
    )


@router.post("/{empresa_id}/sucursales", response_model=SucursalResponse, status_code=status.HTTP_201_CREATED)
def crear_sucursal(
    empresa_id: int,
    payload: SucursalCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> Sucursal:
    verificar_acceso_empresa(usuario, empresa_id)
    _obtener_empresa_o_404(db, empresa_id)

    sucursal = Sucursal(**payload.model_dump(), tenant_id=usuario.tenant_id, empresa_id=empresa_id, activo=True)
    db.add(sucursal)
    db.commit()
    db.refresh(sucursal)
    return sucursal


@router.put("/{empresa_id}/sucursales/{sucursal_id}", response_model=SucursalResponse)
def actualizar_sucursal(
    empresa_id: int,
    sucursal_id: int,
    payload: SucursalCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> Sucursal:
    verificar_acceso_empresa(usuario, empresa_id)
    sucursal = db.get(Sucursal, sucursal_id)
    if sucursal is None or sucursal.empresa_id != empresa_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sucursal no encontrada")

    for campo, valor in payload.model_dump().items():
        setattr(sucursal, campo, valor)
    db.commit()
    db.refresh(sucursal)
    return sucursal
