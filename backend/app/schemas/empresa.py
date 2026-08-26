from typing import Literal

from pydantic import BaseModel, ConfigDict


class EmpresaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rnc: str
    razon_social: str
    nombre_comercial: str | None


class SucursalCreate(BaseModel):
    codigo: str
    nombre: str
    tipo: Literal["finca", "oficina", "proyecto"]
    direccion: str | None = None
    gerente: str | None = None


class SucursalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    codigo: str
    nombre: str
    tipo: str
