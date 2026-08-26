import uuid
from datetime import date

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Factura(Base):
    __tablename__ = "facturas"
    __table_args__ = (
        CheckConstraint("tipo_factura IN ('local','exportacion')", name="facturas_tipo_factura_check"),
        CheckConstraint(
            "estado_ecf IN ('pendiente','aceptado','rechazado','no_aplica')",
            name="facturas_estado_ecf_check",
        ),
        CheckConstraint(
            "NOT (lote_id IS NOT NULL AND obra_id IS NOT NULL)",
            name="facturas_lote_o_obra_check",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=False)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=False)
    tipo_factura: Mapped[str] = mapped_column(String(20), nullable=False)
    e_ncf: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tipo_ecf: Mapped[str | None] = mapped_column(String(5), nullable=True)
    fecha_emision: Mapped[date] = mapped_column(Date, nullable=False)
    moneda: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    itbis_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    itbis_monto: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    estado_ecf: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    lote_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("lotes_cosecha.id"), nullable=True)
    obra_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("obras.id"), nullable=True)
    asiento_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("asientos.id"), nullable=True)


class FacturaDetalle(Base):
    __tablename__ = "factura_detalle"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    factura_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("facturas.id", ondelete="CASCADE"), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(String(200), nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    monto: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
