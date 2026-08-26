from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReglaContabilizacionBase(BaseModel):
    empresa_id: int
    origen_tipo: str
    codigo_evento: str
    numero_cta: str
    debcred: Literal["D", "C"]


class ReglaContabilizacionCreate(ReglaContabilizacionBase):
    pass


class ReglaContabilizacionResponse(ReglaContabilizacionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
