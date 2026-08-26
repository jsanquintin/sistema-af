import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LoteCosecha(Base):
    __tablename__ = "lotes_cosecha"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('disponible','en_proceso','vendido','exportado')",
            name="lotes_cosecha_estado_check",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=False)
    almacen_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("almacenes.id"), nullable=True)
    producto: Mapped[str] = mapped_column(String(50), nullable=False)
    fecha_cosecha: Mapped[date] = mapped_column(Date, nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    unidad: Mapped[str] = mapped_column(String(10), nullable=False, default="qq")
    calidad_grado: Mapped[str | None] = mapped_column(String(30), nullable=True)
    humedad_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    costo_acumulado: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="disponible")
