from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.acceso import verificar_acceso_empresa
from app.core.deps import get_current_user, get_tenant_db
from app.models.factura import Factura, FacturaDetalle
from app.models.usuario import Usuario
from app.schemas.factura import FacturaCreate, FacturaDetalleResponse, FacturaResponse
from app.services.facturacion import crear_factura

router = APIRouter(prefix="/facturas", tags=["facturas"])


def _con_lineas(db: Session, factura: Factura) -> FacturaResponse:
    lineas = list(db.execute(select(FacturaDetalle).where(FacturaDetalle.factura_id == factura.id)).scalars())
    return FacturaResponse(
        id=factura.id,
        empresa_id=factura.empresa_id,
        sucursal_id=factura.sucursal_id,
        cliente_id=factura.cliente_id,
        tipo_factura=factura.tipo_factura,
        e_ncf=factura.e_ncf,
        tipo_ecf=factura.tipo_ecf,
        fecha_emision=factura.fecha_emision,
        moneda=factura.moneda,
        subtotal=factura.subtotal,
        itbis_pct=factura.itbis_pct,
        itbis_monto=factura.itbis_monto,
        total=factura.total,
        estado_ecf=factura.estado_ecf,
        lote_id=factura.lote_id,
        asiento_id=factura.asiento_id,
        lineas=[FacturaDetalleResponse.model_validate(l) for l in lineas],
    )


@router.get("", response_model=list[FacturaResponse])
def listar_facturas(
    empresa_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[FacturaResponse]:
    verificar_acceso_empresa(usuario, empresa_id)
    facturas = list(db.execute(select(Factura).where(Factura.empresa_id == empresa_id)).scalars())
    return [_con_lineas(db, f) for f in facturas]


@router.post("", response_model=FacturaResponse, status_code=status.HTTP_201_CREATED)
def crear(
    payload: FacturaCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> FacturaResponse:
    verificar_acceso_empresa(usuario, payload.empresa_id)
    try:
        factura = crear_factura(db, payload, tenant_id=usuario.tenant_id)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _con_lineas(db, factura)
