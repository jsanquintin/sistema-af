"""Facturacion -> Inventario + Contabilidad (cadena documentada en
docs/designs/nucleo-contabilidad-nomina.md, seccion "Integracion
diferida"): emitir una factura genera el asiento contable via
reglas_contabilizacion y, si trae un lote, la salida de inventario
correspondiente -- no son pasos manuales separados.

Dos objetos costeables posibles, dos formas distintas de reconocer el
costo de venta (una factura no puede traer los dos a la vez, ver
FacturaCreate): un lote de cosecha se vende entero -> se reconoce todo
su costo_acumulado en esa unica factura; una obra se factura por
avances a lo largo del tiempo -> se reconoce solo lo incurrido desde la
ultima factura (costo_acumulado - costo_reconocido).
"""
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.factura import Factura, FacturaDetalle
from app.models.inventario_movimiento import InventarioMovimiento
from app.models.lote_cosecha import LoteCosecha
from app.models.obra import Obra
from app.models.secuencia_ecf import SecuenciaEcf
from app.schemas.factura import FacturaCreate
from app.services.contabilizacion import LineaEvento, generar_asiento_automatico

ITBIS_PCT_LOCAL = 18.0
ITBIS_PCT_EXPORTACION = 0.0


def _tipo_ecf_para(tipo_factura: str, cliente: Cliente) -> str:
    if tipo_factura == "exportacion":
        return "46"  # e-CF de exportacion
    return "31" if cliente.rnc_cedula else "32"  # credito fiscal (con RNC) vs. consumo


def _tomar_siguiente_ecf(db: Session, *, tenant_id: uuid.UUID, sucursal_id: int, tipo_ecf: str) -> str:
    secuencia = db.execute(
        select(SecuenciaEcf)
        .where(
            SecuenciaEcf.tenant_id == tenant_id,
            SecuenciaEcf.sucursal_id == sucursal_id,
            SecuenciaEcf.tipo_ecf == tipo_ecf,
        )
        .with_for_update()
    ).scalar_one_or_none()

    if secuencia is None:
        raise ValueError(
            f"No hay secuencia e-CF configurada para sucursal {sucursal_id}, tipo {tipo_ecf} -- "
            "el proveedor autorizado DGII/OFV asigna el rango antes de poder facturar "
            "(ver NOTA DE DISENO #3 en schema_agrocasa_creixa.sql)"
        )
    if secuencia.proximo_numero > secuencia.numero_max:
        raise ValueError(f"Secuencia e-CF agotada para sucursal {sucursal_id}, tipo {tipo_ecf}")
    if secuencia.fecha_vencimiento is not None and secuencia.fecha_vencimiento < date.today():
        raise ValueError(f"Secuencia e-CF vencida para sucursal {sucursal_id}, tipo {tipo_ecf}")

    numero = secuencia.proximo_numero
    secuencia.proximo_numero = numero + 1
    return f"E{tipo_ecf}{numero:010d}"


def crear_factura(db: Session, payload: FacturaCreate, *, tenant_id: uuid.UUID) -> Factura:
    cliente = db.get(Cliente, payload.cliente_id)
    if cliente is None:
        raise ValueError(f"Cliente {payload.cliente_id} no encontrado")

    lote: LoteCosecha | None = None
    if payload.lote_id is not None:
        lote = db.get(LoteCosecha, payload.lote_id)
        if lote is None:
            raise ValueError(f"Lote {payload.lote_id} no encontrado")

    obra: Obra | None = None
    if payload.obra_id is not None:
        obra = db.get(Obra, payload.obra_id)
        if obra is None:
            raise ValueError(f"Obra {payload.obra_id} no encontrada")

    subtotal = round(sum(l.cantidad * l.precio_unitario for l in payload.lineas), 2)
    itbis_pct = ITBIS_PCT_EXPORTACION if payload.tipo_factura == "exportacion" else ITBIS_PCT_LOCAL
    itbis_monto = round(subtotal * itbis_pct / 100, 2)
    total = round(subtotal + itbis_monto, 2)

    tipo_ecf = _tipo_ecf_para(payload.tipo_factura, cliente)
    e_ncf = _tomar_siguiente_ecf(db, tenant_id=tenant_id, sucursal_id=payload.sucursal_id, tipo_ecf=tipo_ecf)

    factura = Factura(
        tenant_id=tenant_id,
        empresa_id=payload.empresa_id,
        sucursal_id=payload.sucursal_id,
        cliente_id=payload.cliente_id,
        tipo_factura=payload.tipo_factura,
        e_ncf=e_ncf,
        tipo_ecf=tipo_ecf,
        fecha_emision=payload.fecha_emision,
        moneda=payload.moneda,
        subtotal=subtotal,
        itbis_pct=itbis_pct,
        itbis_monto=itbis_monto,
        total=total,
        estado_ecf="pendiente",
        lote_id=payload.lote_id,
        obra_id=payload.obra_id,
    )
    db.add(factura)
    db.flush()  # necesita factura.id para el detalle y la referencia del movimiento

    for linea in payload.lineas:
        db.add(
            FacturaDetalle(
                tenant_id=tenant_id,
                factura_id=factura.id,
                descripcion=linea.descripcion,
                cantidad=linea.cantidad,
                precio_unitario=linea.precio_unitario,
                monto=round(linea.cantidad * linea.precio_unitario, 2),
            )
        )

    movimiento: InventarioMovimiento | None = None
    if lote is not None:
        movimiento = InventarioMovimiento(
            tenant_id=tenant_id,
            lote_id=lote.id,
            tipo_movimiento="salida",
            almacen_origen_id=lote.almacen_id,
            cantidad=lote.cantidad,
            referencia_doc=e_ncf,
            fecha=payload.fecha_emision,
        )
        db.add(movimiento)
        lote.estado = "vendido" if payload.tipo_factura == "local" else "exportado"

    eventos = [
        LineaEvento("VENTA_TOTAL", monto=total, sucursal_id=payload.sucursal_id),
        LineaEvento(
            "VENTA_LOCAL" if payload.tipo_factura == "local" else "VENTA_EXPORT",
            monto=subtotal,
            sucursal_id=payload.sucursal_id,
        ),
    ]
    if itbis_monto > 0:
        eventos.append(LineaEvento("ITBIS_18", monto=itbis_monto, sucursal_id=payload.sucursal_id))
    if lote is not None and float(lote.costo_acumulado) > 0:
        eventos.append(
            LineaEvento("COSTO_VENTA", monto=round(float(lote.costo_acumulado), 2), sucursal_id=payload.sucursal_id)
        )
    costo_obra_a_reconocer = 0.0
    if obra is not None:
        # Una obra se factura por avances, no se vende entera de una vez
        # como un lote -- se reconoce solo lo incurrido desde la ultima
        # factura contra esta obra (costo_acumulado - costo_reconocido),
        # no todo costo_acumulado cada vez.
        costo_obra_a_reconocer = round(float(obra.costo_acumulado) - float(obra.costo_reconocido), 2)
        if costo_obra_a_reconocer > 0:
            eventos.append(
                LineaEvento("COSTO_VENTA", monto=costo_obra_a_reconocer, sucursal_id=payload.sucursal_id)
            )

    # generar_asiento_automatico hace el commit final: si tiene exito,
    # confirma en el mismo commit la factura/detalle/movimiento ya
    # flusheados arriba (misma transaccion de sesion); si falla, el
    # llamador (capa de API) hace rollback de todo junto -- no queda una
    # factura sin su asiento.
    asiento = generar_asiento_automatico(
        db,
        tenant_id=tenant_id,
        empresa_id=payload.empresa_id,
        origen_tipo="factura",
        origen_id=factura.id,
        fecha=payload.fecha_emision,
        descripcion=f"Factura {e_ncf}",
        eventos=eventos,
    )

    factura.asiento_id = asiento.id
    if movimiento is not None:
        movimiento.asiento_id = asiento.id
    if obra is not None and costo_obra_a_reconocer > 0:
        obra.costo_reconocido = float(obra.costo_reconocido) + costo_obra_a_reconocer
    db.commit()
    db.refresh(factura)
    return factura
