from typing import Literal

from pydantic import BaseModel, ConfigDict


class PlanCuentaCreate(BaseModel):
    empresa_id: int
    numero_cta: str
    nivel: int
    # 1 Activo 2 Pasivo 3 Patrimonio 4 Ingreso 5 Costo 6 Gasto -- mismo
    # significado que en schema_agrocasa_creixa.sql, no reinterpretado.
    tipo_cta: Literal[1, 2, 3, 4, 5, 6]
    nombre: str


class PlanCuentaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    numero_cta: str
    nivel: int
    tipo_cta: int
    nombre: str
    activo: bool
