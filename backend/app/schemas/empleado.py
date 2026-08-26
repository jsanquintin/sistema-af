from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


class EmpleadoBase(BaseModel):
    empresa_id: int
    sucursal_id: int | None = None
    cedula: str | None = None
    nombre_completo: str
    tipo_empleado: Literal["fijo", "jornalero"]
    incluye_tss: bool = True
    salario_base: float | None = None
    tarifa_unidad: float | None = None
    fecha_ingreso: date | None = None
    fecha_salida: date | None = None


class EmpleadoCreate(EmpleadoBase):
    pass


class EmpleadoResponse(EmpleadoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activo: bool
