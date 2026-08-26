import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Obra(Base):
    """Proyecto de construccion (Creixa) -- equivalente a un LoteCosecha
    (Agrocasa) como objeto costeable, pero se factura por avances en vez
    de venderse entero de una vez: ver costo_reconocido en
    app/services/facturacion.py.
    """

    __tablename__ = "obras"
    __table_args__ = (
        CheckConstraint("estado IN ('en_proceso','cerrada')", name="obras_estado_check"),
        CheckConstraint("costo_reconocido <= costo_acumulado", name="obras_costo_reconocido_check"),
        UniqueConstraint("tenant_id", "codigo", name="obras_tenant_id_codigo_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=False, unique=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    monto_contrato: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    moneda: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin_estimada: Mapped[date | None] = mapped_column(Date, nullable=True)
    costo_acumulado: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    costo_reconocido: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="en_proceso")
