"""Calculo de nomina: bruto, TSS (empleado + patronal), ISR, neto.

Metodo de ISR: anualizacion sobre 360 dias (convencion DGII para
retencion sobre asalariados, Norma 05-2019) -- se anualiza el sueldo
gravable del periodo, se aplica la tabla progresiva de 4 tramos, y el
impuesto anual resultante se prorratea de vuelta al periodo. Los montos
de corte de cada tramo y las tasas de TSS viven en parametros_nomina
(ver alembic 0004_parametros_nomina) -- **verificar esos valores contra
la tabla DGII/TSS vigente antes de correr nomina real**, la estructura de
cuatro tramos es estable pero los umbrales se ajustan por decreto.
"""
from dataclasses import dataclass
from datetime import date

from app.models.empleado import Empleado
from app.models.parametro_nomina import ParametroNomina

DIAS_MES_CONVENCIONAL = 30
DIAS_ANIO_CONVENCIONAL = 360


@dataclass
class ResultadoNomina:
    monto_bruto: float
    retencion_isr: float
    retencion_tss_empleado: float
    tss_patronal: float
    infotep: float
    riesgos_laborales: float
    monto_neto: float


def _calcular_isr_anual(sueldo_anualizado: float, p: ParametroNomina) -> float:
    t1, t2, t3 = float(p.isr_tramo1_hasta), float(p.isr_tramo2_hasta), float(p.isr_tramo3_hasta)
    tasa2, tasa3, tasa4 = float(p.isr_tramo2_tasa) / 100, float(p.isr_tramo3_tasa) / 100, float(p.isr_tramo4_tasa) / 100

    if sueldo_anualizado <= t1:
        return 0.0
    if sueldo_anualizado <= t2:
        return (sueldo_anualizado - t1) * tasa2

    monto_tramo2 = (t2 - t1) * tasa2
    if sueldo_anualizado <= t3:
        return monto_tramo2 + (sueldo_anualizado - t2) * tasa3

    monto_tramo3 = monto_tramo2 + (t3 - t2) * tasa3
    return monto_tramo3 + (sueldo_anualizado - t3) * tasa4


def calcular_linea(
    empleado: Empleado,
    *,
    dias_unidades: float | None,
    periodo_inicio: date,
    periodo_fin: date,
    parametros: ParametroNomina,
) -> ResultadoNomina:
    dias_periodo = (periodo_fin - periodo_inicio).days + 1
    if dias_periodo <= 0:
        raise ValueError("periodo_fin debe ser posterior o igual a periodo_inicio")

    if empleado.tipo_empleado == "fijo":
        if empleado.salario_base is None:
            raise ValueError(f"Empleado {empleado.id} es fijo pero no tiene salario_base")
        # salario_base se asume mensual; se prorratea sobre el mes
        # convencional de 30 dias segun la duracion real del periodo
        # (permite corridas quincenales sin una columna de periodicidad).
        bruto = float(empleado.salario_base) * (dias_periodo / DIAS_MES_CONVENCIONAL)
    elif empleado.tipo_empleado == "jornalero":
        if dias_unidades is None:
            raise ValueError(f"Empleado {empleado.id} es jornalero, dias_unidades es obligatorio")
        if empleado.tarifa_unidad is None:
            raise ValueError(f"Empleado {empleado.id} es jornalero pero no tiene tarifa_unidad")
        bruto = float(empleado.tarifa_unidad) * dias_unidades
    else:
        raise ValueError(f"tipo_empleado desconocido: {empleado.tipo_empleado}")

    tss_empleado = tss_patronal = infotep = riesgos_laborales = 0.0

    if empleado.incluye_tss:
        salario_minimo = float(parametros.salario_minimo_referencia)
        tope_sfs = salario_minimo * parametros.tss_tope_sfs_salarios_minimos * (dias_periodo / DIAS_MES_CONVENCIONAL)
        tope_afp = salario_minimo * parametros.tss_tope_afp_salarios_minimos * (dias_periodo / DIAS_MES_CONVENCIONAL)
        base_sfs = min(bruto, tope_sfs)
        base_afp = min(bruto, tope_afp)

        tss_empleado = base_sfs * (float(parametros.tss_sfs_empleado_pct) / 100) + base_afp * (
            float(parametros.tss_afp_empleado_pct) / 100
        )
        tss_patronal = base_sfs * (float(parametros.tss_sfs_patronal_pct) / 100) + base_afp * (
            float(parametros.tss_afp_patronal_pct) / 100
        )
        # INFOTEP y riesgos laborales no tienen tope de salario cotizable
        # como SFS/AFP -- aplican sobre el bruto completo del periodo.
        infotep = bruto * (float(parametros.tss_infotep_pct) / 100)
        riesgos_laborales = bruto * (float(parametros.tss_riesgos_laborales_pct) / 100)

    # ISR se calcula sobre el bruto YA NETO de TSS del empleado (la
    # contribucion TSS del empleado reduce la base gravable).
    base_gravable = bruto - tss_empleado
    sueldo_anualizado = base_gravable * (DIAS_ANIO_CONVENCIONAL / dias_periodo)
    isr_anual = _calcular_isr_anual(sueldo_anualizado, parametros)
    retencion_isr = isr_anual * (dias_periodo / DIAS_ANIO_CONVENCIONAL)

    monto_neto = bruto - retencion_isr - tss_empleado

    return ResultadoNomina(
        monto_bruto=round(bruto, 2),
        retencion_isr=round(retencion_isr, 2),
        retencion_tss_empleado=round(tss_empleado, 2),
        tss_patronal=round(tss_patronal, 2),
        infotep=round(infotep, 2),
        riesgos_laborales=round(riesgos_laborales, 2),
        monto_neto=round(monto_neto, 2),
    )
