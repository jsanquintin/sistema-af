from pydantic import BaseModel, ConfigDict


class EmpresaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rnc: str
    razon_social: str
    nombre_comercial: str | None


class SucursalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    codigo: str
    nombre: str
    tipo: str
