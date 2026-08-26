import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlanCuenta(Base):
    """Catalogo de cuentas, por empresa (no solo por tenant) desde la
    Resolucion experta de Open Question 5 -- Agrocasa (agroexportacion) y
    Creixa (inversiones) son giros de negocio sin overlap real de cuentas.
    """

    __tablename__ = "plan_cuentas"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "empresa_id", "numero_cta", name="plan_cuentas_tenant_empresa_numero_cta_key"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False)
    numero_cta: Mapped[str] = mapped_column(String(20), nullable=False)
    nivel: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    tipo_cta: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
