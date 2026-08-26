from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: int | None
    email: str
    nombre_completo: str
    rol: Literal["admin", "contador", "nomina", "facturacion", "consulta"]
    activo: bool


class RestablecerPasswordRequest(BaseModel):
    nueva_password: str = Field(min_length=8)
