from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_db
from app.models.plan_cuenta import PlanCuenta
from app.schemas.plan_cuenta import PlanCuentaResponse

router = APIRouter(prefix="/plan-cuentas", tags=["plan-cuentas"])


@router.get("", response_model=list[PlanCuentaResponse])
def listar_plan_cuentas(db: Session = Depends(get_tenant_db)) -> list[PlanCuenta]:
    # No hay filtro de tenant_id aqui a proposito -- lo aplica RLS via
    # app.tenant_id, fijado en get_tenant_db antes de llegar a este punto.
    return list(db.execute(select(PlanCuenta).where(PlanCuenta.activo.is_(True))).scalars().all())
