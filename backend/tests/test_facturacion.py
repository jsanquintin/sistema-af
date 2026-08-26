import uuid
from datetime import date
from unittest.mock import MagicMock, patch

from app.models.cliente import Cliente
from app.models.obra import Obra
from app.models.secuencia_ecf import SecuenciaEcf
from app.schemas.factura import FacturaCreate, FacturaDetalleCreate
from app.services import facturacion


def _fake_secuencia(**kw):
    defaults = dict(
        id=1, tenant_id=uuid.uuid4(), sucursal_id=1, tipo_ecf="32", proximo_numero=1, numero_max=1000,
        fecha_vencimiento=None,
    )
    defaults.update(kw)
    return SecuenciaEcf(**defaults)


def test_crear_factura_reconoce_solo_el_delta_de_costo_de_la_obra():
    """Una obra se factura por avances -- ya se le cargaron 500 de costo
    acumulado (via nomina) y una factura anterior ya reconocio 200 de eso.
    Esta factura debe reconocer solo el delta (300), no los 500 completos.
    """
    tenant_id = uuid.uuid4()
    cliente = Cliente(id=5, tenant_id=tenant_id, empresa_id=11, nombre="Cliente X", pais="RD", es_exterior=False)
    obra = Obra(
        id=7, tenant_id=tenant_id, empresa_id=11, sucursal_id=1, cliente_id=5, codigo="OBRA-1", nombre="Torre X",
        monto_contrato=1000, moneda="DOP", fecha_inicio=date(2026, 1, 1), costo_acumulado=500, costo_reconocido=200,
        estado="en_proceso",
    )
    secuencia = _fake_secuencia()

    db = MagicMock()
    db.get.side_effect = lambda modelo, pk: {Cliente: cliente, Obra: obra}.get(modelo)
    db.execute.return_value.scalar_one_or_none.return_value = secuencia

    payload = FacturaCreate(
        empresa_id=11,
        sucursal_id=1,
        cliente_id=5,
        tipo_factura="local",
        fecha_emision=date(2026, 8, 26),
        obra_id=7,
        lineas=[FacturaDetalleCreate(descripcion="Avance de obra 30%", cantidad=1, precio_unitario=300)],
    )

    fake_asiento = MagicMock(id=99)
    with patch("app.services.facturacion.generar_asiento_automatico", return_value=fake_asiento) as mock_generar:
        factura = facturacion.crear_factura(db, payload, tenant_id=tenant_id)

    eventos = mock_generar.call_args.kwargs["eventos"]
    costo_venta = [e for e in eventos if e.codigo_evento == "COSTO_VENTA"]
    assert len(costo_venta) == 1
    assert costo_venta[0].monto == 300  # 500 acumulado - 200 ya reconocido, no los 500 completos

    assert obra.costo_reconocido == 500  # se actualiza al total ya reconocido tras postear
    assert factura.obra_id == 7
    assert factura.asiento_id == 99


def test_crear_factura_sin_costo_incurrido_no_genera_costo_venta():
    """Si no se ha cargado costo nuevo desde la ultima factura (delta 0),
    no debe generarse un evento COSTO_VENTA de monto 0."""
    tenant_id = uuid.uuid4()
    cliente = Cliente(id=5, tenant_id=tenant_id, empresa_id=11, nombre="Cliente X", pais="RD", es_exterior=False)
    obra = Obra(
        id=7, tenant_id=tenant_id, empresa_id=11, sucursal_id=1, cliente_id=5, codigo="OBRA-1", nombre="Torre X",
        monto_contrato=1000, moneda="DOP", fecha_inicio=date(2026, 1, 1), costo_acumulado=200, costo_reconocido=200,
        estado="en_proceso",
    )
    db = MagicMock()
    db.get.side_effect = lambda modelo, pk: {Cliente: cliente, Obra: obra}.get(modelo)
    db.execute.return_value.scalar_one_or_none.return_value = _fake_secuencia()

    payload = FacturaCreate(
        empresa_id=11,
        sucursal_id=1,
        cliente_id=5,
        tipo_factura="local",
        fecha_emision=date(2026, 8, 26),
        obra_id=7,
        lineas=[FacturaDetalleCreate(descripcion="Avance de obra", cantidad=1, precio_unitario=300)],
    )

    with patch("app.services.facturacion.generar_asiento_automatico", return_value=MagicMock(id=99)) as mock_generar:
        facturacion.crear_factura(db, payload, tenant_id=tenant_id)

    eventos = mock_generar.call_args.kwargs["eventos"]
    assert not any(e.codigo_evento == "COSTO_VENTA" for e in eventos)
    assert obra.costo_reconocido == 200  # sin cambio
