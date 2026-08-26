import uuid
from datetime import date

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NominaCorrida(Base):
    __tablename__ = "nomina_corridas"
    __table_args__ = (
        CheckConstraint("costeable_tipo IN ('lote','obra')", name="nomina_corridas_costeable_tipo_check"),
        CheckConstraint(
            "(costeable_tipo IS NULL) = (costeable_id IS NULL)",
            name="nomina_corridas_costeable_check",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False)
    sucursal_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=True)
    codigo: Mapped[str] = mapped_column(String(10), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    periodo_inicio: Mapped[date] = mapped_column(nullable=False)
    periodo_fin: Mapped[date] = mapped_column(nullable=False)
    incluye_tss: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cerrada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    asiento_id: Mapped[int | None] = mapped_column(ForeignKey("asientos.id"), nullable=True)
    # Sin FK real a proposito -- polimorfico segun costeable_tipo (lotes_cosecha
    # u obras), mismo patron que asientos.origen_id en el schema original.
    # El costo de mano de obra de la corrida se acumula aqui al cerrarla
    # (ver app/api/nomina.py::cerrar_corrida) -- toda la corrida a un solo
    # costeable, sin prorrateo por linea.
    costeable_tipo: Mapped[str | None] = mapped_column(String(10), nullable=True)
    costeable_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class NominaDetalle(Base):
    """Una fila por empleado en una corrida.

    tss_patronal/infotep/riesgos_laborales (costo del empleador, no
    retencion) no se persisten aqui -- no son parte del schema original y
    son valores derivados deterministicos (monto_bruto x tasa vigente en
    parametros_nomina). Se recalculan en el momento de generar el asiento
    de la corrida (app/services/contabilizacion.py), no se guardan
    dos veces.
    """

    __tablename__ = "nomina_detalle"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nomina_corrida_id: Mapped[int] = mapped_column(
        ForeignKey("nomina_corridas.id", ondelete="CASCADE"), nullable=False
    )
    empleado_id: Mapped[int] = mapped_column(Integer, ForeignKey("empleados.id"), nullable=False)
    sucursal_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=True)
    dias_unidades: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    monto_bruto: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    retencion_isr: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    retencion_tss: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    monto_neto: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
