from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FacturaDetalleCreate(BaseModel):
    descripcion: str
    cantidad: float = Field(gt=0)
    precio_unitario: float = Field(gt=0)


class FacturaDetalleResponse(FacturaDetalleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    monto: float


class FacturaCreate(BaseModel):
    empresa_id: int
    sucursal_id: int
    cliente_id: int
    tipo_factura: Literal["local", "exportacion"]
    fecha_emision: date
    moneda: str = "DOP"
    lote_id: int | None = None
    lineas: list[FacturaDetalleCreate] = Field(min_length=1)


class FacturaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    sucursal_id: int
    cliente_id: int
    tipo_factura: Literal["local", "exportacion"]
    e_ncf: str | None
    tipo_ecf: str | None
    fecha_emision: date
    moneda: str
    subtotal: float
    itbis_pct: float
    itbis_monto: float
    total: float
    estado_ecf: Literal["pendiente", "aceptado", "rechazado", "no_aplica"]
    lote_id: int | None
    asiento_id: int | None
    lineas: list[FacturaDetalleResponse] = []
