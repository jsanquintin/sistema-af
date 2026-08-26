from pydantic import BaseModel, ConfigDict


class AlmacenBase(BaseModel):
    sucursal_id: int
    codigo: str
    nombre: str


class AlmacenCreate(AlmacenBase):
    pass


class AlmacenResponse(AlmacenBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activo: bool
