import uuid

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Superadmin(Base):
    __tablename__ = "superadmins"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    hash_password: Mapped[str] = mapped_column(String(200), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
