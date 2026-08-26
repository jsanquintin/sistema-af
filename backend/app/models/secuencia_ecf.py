import uuid
from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SecuenciaEcf(Base):
    __tablename__ = "secuencias_ecf"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sucursal_id", "tipo_ecf", name="secuencias_ecf_tenant_sucursal_tipo_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=False)
    tipo_ecf: Mapped[str] = mapped_column(String(5), nullable=False)
    proximo_numero: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    numero_max: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
