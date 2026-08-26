from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


class LoteCosechaBase(BaseModel):
    sucursal_id: int
    almacen_id: int | None = None
    producto: str
    fecha_cosecha: date
    cantidad: float
    unidad: str = "qq"
    calidad_grado: str | None = None
    humedad_pct: float | None = None


class LoteCosechaCreate(LoteCosechaBase):
    pass


class LoteCosechaResponse(LoteCosechaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    costo_acumulado: float
    estado: Literal["disponible", "en_proceso", "vendido", "exportado"]
