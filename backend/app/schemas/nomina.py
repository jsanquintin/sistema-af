from datetime import date

from pydantic import BaseModel, ConfigDict


class NominaCorridaCreate(BaseModel):
    empresa_id: int
    sucursal_id: int | None = None
    codigo: str
    nombre: str
    periodo_inicio: date
    periodo_fin: date
    incluye_tss: bool = True


class NominaCorridaResponse(NominaCorridaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cerrada: bool
    asiento_id: int | None


class CalcularNominaRequest(BaseModel):
    # dias_unidades por empleado, solo obligatorio para jornaleros (tareas
    # o dias trabajados en el periodo) -- los fijos no necesitan entrada,
    # su bruto sale de salario_base prorrateado por la duracion del periodo.
    dias_por_empleado: dict[int, float] = {}


class NominaDetalleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empleado_id: int
    sucursal_id: int | None
    dias_unidades: float | None
    monto_bruto: float
    retencion_isr: float
    retencion_tss: float
    monto_neto: float
