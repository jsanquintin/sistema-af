import uuid

from sqlalchemy import CHAR, CheckConstraint, ForeignKey, ForeignKeyConstraint, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReglaContabilizacion(Base):
    """Reglas de mapeo evento->cuenta (equivalente generalizado a GENTRANSNOM).

    Por empresa (no solo por tenant): Agrocasa y Creixa tienen catalogos
    de cuentas separados (ver plan_cuenta.py), asi que el mismo
    codigo_evento (ej. JORNALES_COSECHA) rutea a cuentas distintas segun
    la empresa.
    """

    __tablename__ = "reglas_contabilizacion"
    __table_args__ = (
        CheckConstraint("debcred IN ('D','C')", name="reglas_contabilizacion_debcred_check"),
        UniqueConstraint(
            "tenant_id",
            "empresa_id",
            "origen_tipo",
            "codigo_evento",
            "numero_cta",
            name="reglas_contabilizacion_tenant_empresa_evento_cta_key",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "empresa_id", "numero_cta"],
            ["plan_cuentas.tenant_id", "plan_cuentas.empresa_id", "plan_cuentas.numero_cta"],
            name="reglas_contabilizacion_plan_cuentas_fkey",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False)
    origen_tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    codigo_evento: Mapped[str] = mapped_column(String(30), nullable=False)
    numero_cta: Mapped[str] = mapped_column(String(20), nullable=False)
    debcred: Mapped[str] = mapped_column(CHAR(1), nullable=False)
