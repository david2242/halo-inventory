import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.audit_item import AuditItem
    from app.models.location import Location
    from app.models.user import User


class EquipmentCategory(str, enum.Enum):
    laptop = "laptop"
    desktop = "desktop"
    printer = "printer"
    phone = "phone"
    tablet = "tablet"
    monitor = "monitor"
    projector = "projector"
    other = "other"


class EquipmentStatus(str, enum.Enum):
    active = "active"
    retired = "retired"


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (
        # Partial unique index: serial_number unique only where not null
        Index(
            "ix_equipment_serial_number_not_null",
            "serial_number",
            unique=True,
            postgresql_where=text("serial_number IS NOT NULL"),
        ),
        Index("ix_equipment_location_status", "location_id", "status"),
        Index("ix_equipment_qr_code", "qr_code", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[EquipmentCategory] = mapped_column(
        Enum(EquipmentCategory, name="equipment_category"), nullable=False
    )
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    qr_code: Mapped[str] = mapped_column(String(36), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False
    )
    room: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[EquipmentStatus] = mapped_column(
        Enum(EquipmentStatus, name="equipment_status"),
        nullable=False,
        server_default="active",
    )
    retired_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retired_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    retirement_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    location: Mapped["Location"] = relationship(back_populates="equipment")
    created_by: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by_id], back_populates="created_equipment"
    )
    retired_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[retired_by_id], back_populates="retired_equipment"
    )
    audit_items: Mapped[List["AuditItem"]] = relationship(
        back_populates="equipment", lazy="select"
    )
