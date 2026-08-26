from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.acceso import verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.asiento import Asiento, AsientoDetalle
from app.models.plan_cuenta import PlanCuenta
from app.models.usuario import Usuario
from app.schemas.reporte import BalanceComprobacionLinea

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("/balance-comprobacion", response_model=list[BalanceComprobacionLinea])
def balance_comprobacion(
    empresa_id: int,
    desde: date,
    hasta: date,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[BalanceComprobacionLinea]:
    verificar_acceso_empresa(usuario, empresa_id)

    # Solo asientos posteados -- un borrador no representa un hecho
    # contable confirmado todavia, no debe aparecer en el balance.
    query = (
        select(
            AsientoDetalle.numero_cta,
            PlanCuenta.nombre,
            func.sum(case((AsientoDetalle.debcred == "D", AsientoDetalle.monto), else_=0)).label("debe"),
            func.sum(case((AsientoDetalle.debcred == "C", AsientoDetalle.monto), else_=0)).label("haber"),
        )
        .join(Asiento, Asiento.id == AsientoDetalle.asiento_id)
        .join(
            PlanCuenta,
            (PlanCuenta.tenant_id == AsientoDetalle.tenant_id)
            & (PlanCuenta.empresa_id == AsientoDetalle.empresa_id)
            & (PlanCuenta.numero_cta == AsientoDetalle.numero_cta),
        )
        .where(
            Asiento.empresa_id == empresa_id,
            Asiento.estado == "posteado",
            Asiento.fecha >= desde,
            Asiento.fecha <= hasta,
        )
        .group_by(AsientoDetalle.numero_cta, PlanCuenta.nombre)
        .order_by(AsientoDetalle.numero_cta)
    )
    filas = db.execute(query).all()
    return [
        BalanceComprobacionLinea(
            numero_cta=numero_cta,
            nombre=nombre,
            debe=float(debe),
            haber=float(haber),
            saldo=round(float(debe) - float(haber), 2),
        )
        for numero_cta, nombre, debe, haber in filas
    ]
