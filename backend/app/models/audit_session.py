import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.audit_item import AuditItem
    from app.models.location import Location
    from app.models.user import User


class AuditSessionStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"


class AuditSession(Base):
    __tablename__ = "audit_sessions"
    __table_args__ = (
        # Ensures at most one in_progress session per location
        Index(
            "ix_audit_sessions_one_open_per_location",
            "location_id",
            unique=True,
            postgresql_where=text("status = 'in_progress'"),
            sqlite_where=text("status = 'in_progress'"),
        ),
        Index("ix_audit_sessions_location_status", "location_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False
    )
    started_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[AuditSessionStatus] = mapped_column(
        Enum(AuditSessionStatus, name="audit_session_status"),
        nullable=False,
        server_default="in_progress",
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    location: Mapped["Location"] = relationship(back_populates="audit_sessions")
    started_by: Mapped["User"] = relationship(back_populates="audit_sessions")
    items: Mapped[List["AuditItem"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="select",
    )
