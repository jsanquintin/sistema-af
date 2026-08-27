import uuid

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SuperadminAuditoria(Base):
    __tablename__ = "superadmin_auditoria"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    superadmin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("superadmins.id"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    detalle: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    creado_en: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
