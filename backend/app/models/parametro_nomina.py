from sqlalchemy import Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParametroNomina(Base):
    """Tramos ISR + tasas TSS por anio fiscal.

    Sin tenant_id a proposito (ver alembic 0004_parametros_nomina): son
    parametros regulatorios nacionales (DGII/TSS), no datos de un tenant
    especifico -- todos los tenants del sistema comparten la misma tabla.
    """

    __tablename__ = "parametros_nomina"

    id: Mapped[int] = mapped_column(primary_key=True)
    anio_fiscal: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    isr_tramo1_hasta: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    isr_tramo2_hasta: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    isr_tramo3_hasta: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    isr_tramo2_tasa: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=15)
    isr_tramo3_tasa: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=20)
    isr_tramo4_tasa: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=25)
    tss_sfs_empleado_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=3.04)
    tss_sfs_patronal_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=7.09)
    tss_afp_empleado_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=2.87)
    tss_afp_patronal_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=7.10)
    tss_riesgos_laborales_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=1.20)
    tss_infotep_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=1.00)
    tss_tope_sfs_salarios_minimos: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=10)
    tss_tope_afp_salarios_minimos: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=20)
    salario_minimo_referencia: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    notas: Mapped[str | None] = mapped_column(String(300), nullable=True)
