from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AsientoDetalleCreate(BaseModel):
    numero_cta: str
    sucursal_id: int | None = None
    debcred: Literal["D", "C"]
    monto: float = Field(gt=0)


class AsientoDetalleResponse(AsientoDetalleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int


class AsientoCreate(BaseModel):
    fecha: date
    descripcion: str | None = None
    lineas: list[AsientoDetalleCreate] = Field(min_length=1)


class AsientoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    fecha: date
    origen_tipo: Literal["factura", "nomina", "manual", "inventario", "apertura"]
    origen_id: int | None
    descripcion: str | None
    creado_por: str | None
    creado_en: datetime
    estado: Literal["borrador", "posteado"]
    lineas: list[AsientoDetalleResponse] = []
