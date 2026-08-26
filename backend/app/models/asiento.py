import uuid
from datetime import date, datetime

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Asiento(Base):
    """Motor de asientos centralizado (equivalente a DETCONT de Soluflex).

    estado empieza en 'borrador' y solo avanza a 'posteado' via
    app/services/contabilizacion.py:postear_asiento, que valida el cuadre
    (debe=haber) antes del cambio -- el trigger de Postgres
    (fn_validar_cuadre_asiento) ya no calcula cuadre, solo bloquea
    cualquier edicion de asiento_detalle una vez posteado.
    """

    __tablename__ = "asientos"
    __table_args__ = (
        CheckConstraint(
            "origen_tipo IN ('factura','nomina','manual','inventario','apertura')",
            name="asientos_origen_tipo_check",
        ),
        CheckConstraint("estado IN ('borrador','posteado')", name="asientos_estado_check"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    origen_tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    origen_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    descripcion: Mapped[str | None] = mapped_column(String(250), nullable=True)
    creado_por: Mapped[str | None] = mapped_column(String(100), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    estado: Mapped[str] = mapped_column(String(10), nullable=False, default="borrador")


class AsientoDetalle(Base):
    __tablename__ = "asiento_detalle"
    __table_args__ = (
        CheckConstraint("debcred IN ('D','C')", name="asiento_detalle_debcred_check"),
        CheckConstraint("monto > 0", name="asiento_detalle_monto_check"),
        ForeignKeyConstraint(
            ["tenant_id", "empresa_id", "numero_cta"],
            ["plan_cuentas.tenant_id", "plan_cuentas.empresa_id", "plan_cuentas.numero_cta"],
            name="asiento_detalle_plan_cuentas_fkey",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    asiento_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("asientos.id", ondelete="CASCADE"), nullable=False)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False)
    numero_cta: Mapped[str] = mapped_column(String(20), nullable=False)
    sucursal_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=True)
    debcred: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    monto: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
