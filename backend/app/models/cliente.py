import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False)
    rnc_cedula: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    pais: Mapped[str] = mapped_column(String(60), nullable=False, default="República Dominicana")
    es_exterior: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
