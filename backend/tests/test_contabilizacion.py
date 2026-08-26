import uuid
from unittest.mock import MagicMock

import pytest

from app.models.asiento import Asiento, AsientoDetalle
from app.models.regla_contabilizacion import ReglaContabilizacion
from app.services import contabilizacion
from app.services.contabilizacion import LineaEvento


def _fake_regla(**kw):
    defaults = dict(
        id=1, tenant_id=uuid.uuid4(), empresa_id=11, origen_tipo="nomina", codigo_evento="X", numero_cta="1",
        debcred="D",
    )
    defaults.update(kw)
    return ReglaContabilizacion(**defaults)


def test_generar_asiento_automatico_falla_antes_de_insertar_si_falta_regla():
    db = MagicMock()
    db.execute.return_value.scalars.return_value = []  # sin reglas configuradas para este origen/empresa

    with pytest.raises(ValueError, match="Sin regla de contabilizacion"):
        contabilizacion.generar_asiento_automatico(
            db,
            tenant_id=uuid.uuid4(),
            empresa_id=11,
            origen_tipo="nomina",
            origen_id=1,
            fecha="2026-08-26",
            descripcion=None,
            eventos=[LineaEvento("JORNALES_COSECHA", monto=100)],
        )

    assert not any(isinstance(c.args[0], Asiento) for c in db.add.call_args_list)


def test_generar_asiento_automatico_hace_batch_fetch_no_n_mas_1():
    db = MagicMock()
    tenant_id = uuid.uuid4()
    reglas = [
        _fake_regla(tenant_id=tenant_id, codigo_evento="JORNALES_COSECHA", numero_cta="60101", debcred="D"),
        _fake_regla(tenant_id=tenant_id, codigo_evento="JORNALES_COSECHA", numero_cta="21001", debcred="C"),
    ]
    db.execute.return_value.scalars.return_value = reglas

    asiento = contabilizacion.generar_asiento_automatico(
        db,
        tenant_id=tenant_id,
        empresa_id=11,
        origen_tipo="nomina",
        origen_id=1,
        fecha="2026-08-26",
        descripcion=None,
        eventos=[
            LineaEvento("JORNALES_COSECHA", monto=100),
            LineaEvento("JORNALES_COSECHA", monto=200),
        ],
    )

    # Una sola query trae TODAS las reglas del origen -- sin importar
    # cuantos eventos compartan el mismo codigo_evento (evita N+1).
    assert db.execute.call_count == 1
    assert asiento.estado == "posteado"


def test_generar_asiento_automatico_rechaza_si_reglas_producen_descuadre():
    db = MagicMock()
    tenant_id = uuid.uuid4()
    # Regla mal configurada: solo el lado debito, sin su contrapartida --
    # nunca puede cuadrar sin importar el evento.
    db.execute.return_value.scalars.return_value = [
        _fake_regla(tenant_id=tenant_id, codigo_evento="ITBIS_18", numero_cta="60101", debcred="D"),
    ]

    with pytest.raises(ValueError, match="descuadrado"):
        contabilizacion.generar_asiento_automatico(
            db,
            tenant_id=tenant_id,
            empresa_id=11,
            origen_tipo="factura",
            origen_id=1,
            fecha="2026-08-26",
            descripcion=None,
            eventos=[LineaEvento("ITBIS_18", monto=180)],
        )


def test_postear_asiento_rechaza_si_no_cuadra():
    db = MagicMock()
    asiento = Asiento(
        id=1, tenant_id=uuid.uuid4(), empresa_id=11, fecha="2026-08-26", origen_tipo="manual", estado="borrador"
    )
    db.execute.return_value.scalars.return_value = [
        AsientoDetalle(
            id=1, tenant_id=asiento.tenant_id, asiento_id=1, empresa_id=11, numero_cta="10101", debcred="D", monto=100
        ),
        AsientoDetalle(
            id=2, tenant_id=asiento.tenant_id, asiento_id=1, empresa_id=11, numero_cta="31001", debcred="C", monto=50
        ),
    ]

    with pytest.raises(ValueError, match="descuadrado"):
        contabilizacion.postear_asiento(db, asiento)

    assert asiento.estado == "borrador"


def test_postear_asiento_marca_posteado_si_cuadra():
    db = MagicMock()
    asiento = Asiento(
        id=1, tenant_id=uuid.uuid4(), empresa_id=11, fecha="2026-08-26", origen_tipo="manual", estado="borrador"
    )
    db.execute.return_value.scalars.return_value = [
        AsientoDetalle(
            id=1, tenant_id=asiento.tenant_id, asiento_id=1, empresa_id=11, numero_cta="10101", debcred="D", monto=100
        ),
        AsientoDetalle(
            id=2, tenant_id=asiento.tenant_id, asiento_id=1, empresa_id=11, numero_cta="31001", debcred="C", monto=100
        ),
    ]

    contabilizacion.postear_asiento(db, asiento)

    assert asiento.estado == "posteado"
