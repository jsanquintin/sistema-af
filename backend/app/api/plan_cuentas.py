from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.acceso import verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.plan_cuenta import PlanCuenta
from app.models.usuario import Usuario
from app.schemas.plan_cuenta import PlanCuentaResponse

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
