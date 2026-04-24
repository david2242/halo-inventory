import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.audit_session import AuditSession
    from app.models.equipment import Equipment


class UserRole(str, enum.Enum):
    director = "director"
    delegate = "delegate"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    created_equipment: Mapped[List["Equipment"]] = relationship(
        "Equipment",
        foreign_keys="Equipment.created_by_id",
        back_populates="created_by",
        lazy="select",
    )
    retired_equipment: Mapped[List["Equipment"]] = relationship(
        "Equipment",
        foreign_keys="Equipment.retired_by_id",
        back_populates="retired_by",
        lazy="select",
    )
    audit_sessions: Mapped[List["AuditSession"]] = relationship(
        back_populates="started_by", lazy="select"
    )
