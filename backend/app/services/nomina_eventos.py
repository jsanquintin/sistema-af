"""Resuelve el codigo_evento de reglas_contabilizacion para una linea de
nomina, a partir de (tipo_empleado, sucursal.tipo) -- ver el diagrama en
docs/designs/nucleo-contabilidad-nomina.md.

Mapeo explicito y cerrado: una combinacion sin entrada levanta ValueError
en vez de un default silencioso (ej. jornalero en una sucursal 'oficina'
no es un caso real del negocio, no se le inventa un evento).
"""
from app.models.empleado import Empleado
from app.models.sucursal import Sucursal
from app.services.contabilizacion import LineaEvento
from app.services.nomina_calculo import ResultadoNomina

_MAPEO_EVENTOS: dict[tuple[str, str], str] = {
    ("jornalero", "finca"): "JORNALES_COSECHA",
    ("jornalero", "proyecto"): "JORNALES_PROYECTO",
    ("fijo", "finca"): "SALARIOS_FINCA",
    ("fijo", "oficina"): "SALARIOS_ADMIN",
    ("fijo", "proyecto"): "SALARIOS_PROYECTO",
}


def resolver_codigo_evento(empleado: Empleado, sucursal: Sucursal) -> str:
    clave = (empleado.tipo_empleado, sucursal.tipo)
    codigo = _MAPEO_EVENTOS.get(clave)
    if codigo is None:
        raise ValueError(
            f"Sin codigo_evento mapeado para tipo_empleado={empleado.tipo_empleado!r} "
            f"en sucursal de tipo={sucursal.tipo!r} (empleado {empleado.id})"
        )
    return codigo


def eventos_para_linea(*, empleado: Empleado, sucursal: Sucursal, resultado: ResultadoNomina) -> list[LineaEvento]:
    """Descompone una linea de nomina calculada en los eventos contables
    que la componen. Un solo bruto no es un evento autobalanceado -- se
    reparte en gasto (D) vs. neto/ISR retenido/TSS retenido (C, tres
    pasivos distintos que suman el bruto por definicion). El costo
    patronal (TSS patronal, INFOTEP, riesgos laborales) es gasto+pasivo
    aparte, cada uno autobalanceado.

    Cada codigo_evento generado aqui necesita su propia fila en
    reglas_contabilizacion (por empresa) antes de poder cerrar una
    corrida -- ver Alcance de v1 en el design doc.
    """
    base = resolver_codigo_evento(empleado, sucursal)
    eventos = [LineaEvento(base, monto=resultado.monto_bruto, sucursal_id=sucursal.id)]

    if resultado.monto_neto > 0:
        eventos.append(LineaEvento(f"{base}_NETO", monto=resultado.monto_neto, sucursal_id=sucursal.id))
    if resultado.retencion_isr > 0:
        eventos.append(LineaEvento(f"{base}_ISR", monto=resultado.retencion_isr, sucursal_id=sucursal.id))
    if resultado.retencion_tss_empleado > 0:
        eventos.append(LineaEvento(f"{base}_TSS", monto=resultado.retencion_tss_empleado, sucursal_id=sucursal.id))
    if resultado.tss_patronal > 0:
        eventos.append(
            LineaEvento(f"{base}_TSS_PATRONAL", monto=resultado.tss_patronal, sucursal_id=sucursal.id)
        )
    if resultado.infotep > 0:
        eventos.append(LineaEvento(f"{base}_INFOTEP", monto=resultado.infotep, sucursal_id=sucursal.id))
    if resultado.riesgos_laborales > 0:
        eventos.append(LineaEvento(f"{base}_RIESGOS", monto=resultado.riesgos_laborales, sucursal_id=sucursal.id))

    return eventos
