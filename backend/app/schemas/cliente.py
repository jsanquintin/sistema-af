from pydantic import BaseModel, ConfigDict


class ClienteBase(BaseModel):
    empresa_id: int
    rnc_cedula: str | None = None
    nombre: str
    pais: str = "República Dominicana"
    es_exterior: bool = False


class ClienteCreate(ClienteBase):
    pass


class ClienteResponse(ClienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
