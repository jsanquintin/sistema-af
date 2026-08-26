import uuid
from datetime import date

import pytest

from app.models.empleado import Empleado
from app.models.parametro_nomina import ParametroNomina
from app.services.nomina_calculo import calcular_linea

# Mismos valores sembrados en alembic 0004_parametros_nomina.
_PARAMETROS = ParametroNomina(
    id=1,
    anio_fiscal=2026,
    isr_tramo1_hasta=416220.00,
    isr_tramo2_hasta=624329.00,
    isr_tramo3_hasta=867123.00,
    isr_tramo2_tasa=15,
    isr_tramo3_tasa=20,
    isr_tramo4_tasa=25,
    tss_sfs_empleado_pct=3.04,
    tss_sfs_patronal_pct=7.09,
    tss_afp_empleado_pct=2.87,
    tss_afp_patronal_pct=7.10,
    tss_riesgos_laborales_pct=1.20,
    tss_infotep_pct=1.00,
    tss_tope_sfs_salarios_minimos=10,
    tss_tope_afp_salarios_minimos=20,
    salario_minimo_referencia=15000.00,
)


def test_fijo_con_tss_bajo_el_umbral_de_isr():
    empleado = Empleado(
        id=1, tenant_id=uuid.uuid4(), empresa_id=11, nombre_completo="Ana", tipo_empleado="fijo", incluye_tss=True,
        salario_base=30000,
    )
    resultado = calcular_linea(
        empleado, dias_unidades=None, periodo_inicio=date(2026, 8, 1), periodo_fin=date(2026, 8, 30),
        parametros=_PARAMETROS,
    )

    assert resultado.monto_bruto == 30000
    assert resultado.retencion_tss_empleado == pytest.approx(30000 * 0.0591, abs=0.01)
    assert resultado.retencion_isr == 0  # anualizado (12x) no cruza el primer tramo
    assert resultado.monto_neto == pytest.approx(30000 - resultado.retencion_tss_empleado, abs=0.01)
    assert resultado.tss_patronal > 0


def test_jornalero_sin_tss_no_retiene_tss():
    empleado = Empleado(
        id=2, tenant_id=uuid.uuid4(), empresa_id=11, nombre_completo="Luis", tipo_empleado="jornalero", incluye_tss=False,
        tarifa_unidad=800,
    )
    resultado = calcular_linea(
        empleado, dias_unidades=12, periodo_inicio=date(2026, 8, 1), periodo_fin=date(2026, 8, 15),
        parametros=_PARAMETROS,
    )

    assert resultado.monto_bruto == 9600
    assert resultado.retencion_tss_empleado == 0
    assert resultado.tss_patronal == 0
    assert resultado.monto_neto == resultado.monto_bruto - resultado.retencion_isr


def test_jornalero_requiere_dias_unidades():
    empleado = Empleado(
        id=3, tenant_id=uuid.uuid4(), empresa_id=11, nombre_completo="Pedro", tipo_empleado="jornalero", incluye_tss=False,
        tarifa_unidad=800,
    )
    with pytest.raises(ValueError, match="dias_unidades"):
        calcular_linea(
            empleado, dias_unidades=None, periodo_inicio=date(2026, 8, 1), periodo_fin=date(2026, 8, 15),
            parametros=_PARAMETROS,
        )


def test_sueldo_alto_cruza_tramos_de_isr():
    empleado = Empleado(
        id=4, tenant_id=uuid.uuid4(), empresa_id=11, nombre_completo="Gerente", tipo_empleado="fijo", incluye_tss=True,
        salario_base=100000,
    )
    resultado = calcular_linea(
        empleado, dias_unidades=None, periodo_inicio=date(2026, 8, 1), periodo_fin=date(2026, 8, 30),
        parametros=_PARAMETROS,
    )

    # Sueldo anualizado (~1,129,080) cae en el tramo de 25% -- debe haber
    # una retencion de ISR sustancial, no cero.
    assert resultado.retencion_isr > 10000
    assert resultado.monto_neto == pytest.approx(
        resultado.monto_bruto - resultado.retencion_isr - resultado.retencion_tss_empleado, abs=0.01
    )
