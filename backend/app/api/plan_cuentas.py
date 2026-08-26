from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.acceso import verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.plan_cuenta import PlanCuenta
from app.models.usuario import Usuario
from app.schemas.plan_cuenta import PlanCuentaCreate, PlanCuentaResponse

router = APIRouter(prefix="/plan-cuentas", tags=["plan-cuentas"])


@router.get("", response_model=list[PlanCuentaResponse])
def listar_plan_cuentas(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[PlanCuenta]:
    # empresa_id ahora es obligatorio: el catalogo es por empresa (Open
    # Question 5 resuelta), Agrocasa y Creixa ya no comparten numeracion.
    # No hay filtro de tenant_id aqui a proposito -- lo aplica RLS via
    # app.tenant_id, fijado en get_tenant_db antes de llegar a este punto.
    verificar_acceso_empresa(usuario, empresa_id)
    query = select(PlanCuenta).where(PlanCuenta.activo.is_(True), PlanCuenta.empresa_id == empresa_id)
    return list(db.execute(query).scalars().all())


@router.post("", response_model=PlanCuentaResponse, status_code=status.HTTP_201_CREATED)
def crear_cuenta(
    payload: PlanCuentaCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> PlanCuenta:
    verificar_acceso_empresa(usuario, payload.empresa_id)
    cuenta = PlanCuenta(**payload.model_dump(), tenant_id=usuario.tenant_id, activo=True)
    db.add(cuenta)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe la cuenta {payload.numero_cta} en esta empresa",
        )
    db.refresh(cuenta)
    return cuenta


@router.put("/{cuenta_id}", response_model=PlanCuentaResponse)
def actualizar_cuenta(
    cuenta_id: int,
    payload: PlanCuentaCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> PlanCuenta:
    cuenta = db.get(PlanCuenta, cuenta_id)
    if cuenta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    verificar_acceso_empresa(usuario, cuenta.empresa_id)
    verificar_acceso_empresa(usuario, payload.empresa_id)

    for campo, valor in payload.model_dump().items():
        setattr(cuenta, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe la cuenta {payload.numero_cta} en esta empresa",
        )
    db.refresh(cuenta)
    return cuenta


@router.delete("/{cuenta_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_cuenta(
    cuenta_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> None:
    cuenta = db.get(PlanCuenta, cuenta_id)
    if cuenta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    verificar_acceso_empresa(usuario, cuenta.empresa_id)

    # Soft-delete -- una cuenta referenciada por asiento_detalle/
    # reglas_contabilizacion no puede desaparecer del catalogo, igual que
    # empleados/almacenes.
    cuenta.activo = False
    db.commit()
