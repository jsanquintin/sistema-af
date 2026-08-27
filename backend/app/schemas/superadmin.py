from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    activo: bool


class TenantCreateRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8)
    admin_nombre_completo: str = Field(min_length=1, max_length=150)


class TenantCreateResponse(BaseModel):
    tenant: TenantResponse
    admin_email: str


class TenantUpdateRequest(BaseModel):
    activo: bool
