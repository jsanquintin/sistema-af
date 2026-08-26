import uuid
from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Empleado(Base):
    __tablename__ = "empleados"
    __table_args__ = (
        CheckConstraint("tipo_empleado IN ('fijo','jornalero')", name="empleados_tipo_empleado_check"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False)
    sucursal_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=True)
    cedula: Mapped[str | None] = mapped_column(String(15), nullable=True)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo_empleado: Mapped[str] = mapped_column(String(15), nullable=False)
    incluye_tss: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    salario_base: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    tarifa_unidad: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    fecha_ingreso: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_salida: Mapped[date | None] = mapped_column(Date, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
