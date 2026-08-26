from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class NominaCorridaCreate(BaseModel):
    empresa_id: int
    sucursal_id: int | None = None
    codigo: str
    nombre: str
    periodo_inicio: date
    periodo_fin: date
    incluye_tss: bool = True
    # Centro de costo al que se le carga el bruto de TODA la corrida al
    # cerrarla (sin prorrateo por linea/empleado) -- ver
    # app/api/nomina.py::cerrar_corrida. Ambos o ninguno.
    costeable_tipo: Literal["lote", "obra"] | None = None
    costeable_id: int | None = None

    @model_validator(mode="after")
    def _costeable_ambos_o_ninguno(self) -> "NominaCorridaCreate":
        if (self.costeable_tipo is None) != (self.costeable_id is None):
            raise ValueError("costeable_tipo y costeable_id deben venir juntos o ninguno")
        return self


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
