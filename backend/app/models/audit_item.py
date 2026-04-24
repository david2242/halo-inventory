import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.audit_session import AuditSession
    from app.models.equipment import Equipment


class CheckMethod(str, enum.Enum):
    scan = "scan"
    manual = "manual"


class AuditItem(Base):
    __tablename__ = "audit_items"
    __table_args__ = (
        UniqueConstraint(
            "audit_session_id",
            "equipment_id",
            name="uq_audit_items_session_equipment",
        ),
        Index("ix_audit_items_session_id", "audit_session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    audit_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_sessions.id", ondelete="CASCADE"), nullable=False
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipment.id", ondelete="RESTRICT"), nullable=False
    )
    check_method: Mapped[Optional[CheckMethod]] = mapped_column(
        Enum(CheckMethod, name="check_method"), nullable=True
    )
    checked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_present: Mapped[Optional[bool]] = mapped_column(nullable=True)

    session: Mapped["AuditSession"] = relationship(back_populates="items")
    equipment: Mapped["Equipment"] = relationship(back_populates="audit_items")
