import uuid
from datetime import date

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InventarioMovimiento(Base):
    """Bitacora de inventario -- append-only a proposito (ver
    app/api/inventario_movimientos.py: no hay UPDATE ni DELETE, una
    correccion se hace con un movimiento contrario, igual que en
    contabilidad real).

    asiento_id (columna real en la tabla, ver schema_agrocasa_creixa.sql)
    no se mapea aqui: lo llenaria el motor de asientos, que todavia no
    existe como modelo -- declarar el FK contra una tabla sin mapear
    rompe la resolucion de SQLAlchemy. La columna se queda NULL via el
    default de Postgres hasta que ese motor exista.
    """

    __tablename__ = "inventario_movimientos"
    __table_args__ = (
        CheckConstraint(
            "tipo_movimiento IN ('entrada','salida','ajuste','merma','traslado')",
            name="inventario_movimientos_tipo_movimiento_check",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    lote_id: Mapped[int] = mapped_column(Integer, ForeignKey("lotes_cosecha.id"), nullable=False)
    tipo_movimiento: Mapped[str] = mapped_column(String(20), nullable=False)
    almacen_origen_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("almacenes.id"), nullable=True)
    almacen_destino_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("almacenes.id"), nullable=True)
    cantidad: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    referencia_doc: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
