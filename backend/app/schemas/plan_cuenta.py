from pydantic import BaseModel, ConfigDict


class PlanCuentaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    numero_cta: str
    nivel: int
    tipo_cta: int
    nombre: str
    activo: bool
