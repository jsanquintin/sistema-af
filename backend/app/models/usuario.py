import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="usuarios_tenant_id_email_key"),
        CheckConstraint(
            "rol IN ('admin','contador','nomina','facturacion','consulta')",
            name="usuarios_rol_check",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    empresa_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    hash_password: Mapped[str] = mapped_column(String(200), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
