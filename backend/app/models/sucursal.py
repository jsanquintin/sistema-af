import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Sucursal(Base):
    """Finca, oficina o proyecto -- centro de costo contable.

    Fusiona lo que en un borrador previo se llamo "fincas/proyectos" (ver
    CONTEXTO.md): verificado contra la tabla SUCURSALES real de Soluflex.
    """

    __tablename__ = "sucursales"
    __table_args__ = (
        UniqueConstraint("empresa_id", "codigo", name="sucursales_empresa_id_codigo_key"),
        CheckConstraint("tipo IN ('finca','oficina','proyecto')", name="sucursales_tipo_check"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    direccion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gerente: Mapped[str | None] = mapped_column(String(150), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
