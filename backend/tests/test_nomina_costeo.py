import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.nomina import _acumular_costo_corrida, _resolver_costeable
from app.models.lote_cosecha import LoteCosecha
from app.models.nomina import NominaCorrida, NominaDetalle
from app.models.obra import Obra


def _fake_corrida(**kw):
    defaults = dict(
        id=1, tenant_id=uuid.uuid4(), empresa_id=11, codigo="Q1", nombre="Nomina",
        periodo_inicio="2026-08-01", periodo_fin="2026-08-15", cerrada=False,
        costeable_tipo=None, costeable_id=None,
    )
    defaults.update(kw)
    return NominaCorrida(**defaults)


def _fake_detalle(*brutos):
    return [
        NominaDetalle(
            id=i, tenant_id=uuid.uuid4(), nomina_corrida_id=1, empleado_id=i, monto_bruto=bruto,
            retencion_isr=0, retencion_tss=0, monto_neto=bruto,
        )
        for i, bruto in enumerate(brutos, start=1)
    ]


def test_resolver_costeable_sin_asignar_devuelve_none():
    db = MagicMock()
    assert _resolver_costeable(db, _fake_corrida()) is None


def test_resolver_costeable_lote_inexistente_devuelve_400():
    db = MagicMock()
    db.get.return_value = None
    corrida = _fake_corrida(costeable_tipo="lote", costeable_id=99)

    with pytest.raises(HTTPException) as exc:
        _resolver_costeable(db, corrida)
    assert exc.value.status_code == 400


def test_resolver_costeable_obra_existente():
    db = MagicMock()
    obra = Obra(
        id=7, tenant_id=uuid.uuid4(), empresa_id=11, sucursal_id=1, cliente_id=5, codigo="OBRA-1", nombre="Torre",
        monto_contrato=1000, fecha_inicio="2026-01-01", costo_acumulado=0, costo_reconocido=0, estado="en_proceso",
    )
    db.get.return_value = obra
    corrida = _fake_corrida(costeable_tipo="obra", costeable_id=7)

    assert _resolver_costeable(db, corrida) is obra
    db.get.assert_called_once_with(Obra, 7)


def test_acumular_costo_corrida_suma_bruto_de_todas_las_lineas_sin_costeable_no_hace_nada():
    _acumular_costo_corrida(None, _fake_detalle(100, 200))  # no debe lanzar ni tener efecto


def test_acumular_costo_corrida_suma_bruto_de_todas_las_lineas_al_costeable():
    obra = Obra(
        id=7, tenant_id=uuid.uuid4(), empresa_id=11, sucursal_id=1, cliente_id=5, codigo="OBRA-1", nombre="Torre",
        monto_contrato=1000, fecha_inicio="2026-01-01", costo_acumulado=50, costo_reconocido=0, estado="en_proceso",
    )
    detalle = _fake_detalle(100, 250.50)  # dos empleados de la corrida

    _acumular_costo_corrida(obra, detalle)

    assert obra.costo_acumulado == 400.50  # 50 previo + 100 + 250.50 de esta corrida


def test_acumular_costo_corrida_funciona_igual_para_lote():
    lote = LoteCosecha(
        id=3, tenant_id=uuid.uuid4(), sucursal_id=1, producto="cafe", fecha_cosecha="2026-08-01", cantidad=120,
        costo_acumulado=0, estado="disponible",
    )
    _acumular_costo_corrida(lote, _fake_detalle(500))
    assert lote.costo_acumulado == 500
