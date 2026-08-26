from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ObraBase(BaseModel):
    empresa_id: int
    sucursal_id: int
    cliente_id: int
    codigo: str
    nombre: str
    monto_contrato: float
    moneda: str = "DOP"
    fecha_inicio: date
    fecha_fin_estimada: date | None = None


class ObraCreate(ObraBase):
    pass


class ObraResponse(ObraBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    costo_acumulado: float
    costo_reconocido: float
    estado: Literal["en_proceso", "cerrada"]
