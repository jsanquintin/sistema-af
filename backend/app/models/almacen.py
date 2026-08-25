import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Almacen(Base):
    """Ubicacion fisica dentro de una sucursal (una sucursal puede tener
    mas de un almacen -- ver ALMACENES de Soluflex en CONTEXTO.md)."""

    __tablename__ = "almacenes"
    __table_args__ = (
        UniqueConstraint("sucursal_id", "codigo", name="almacenes_sucursal_id_codigo_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
