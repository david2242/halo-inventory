import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.equipment import Equipment, EquipmentCategory, EquipmentStatus
from app.repositories.base import BaseRepository


class EquipmentRepository(BaseRepository[Equipment]):
    def __init__(self, db: Session) -> None:
        super().__init__(Equipment, db)

    def get_by_qr_code(self, qr_code: str) -> Optional[Equipment]:
        return self.db.scalar(select(Equipment).where(Equipment.qr_code == qr_code))

    def get_by_serial_number(self, serial_number: str) -> Optional[Equipment]:
        return self.db.scalar(
            select(Equipment).where(Equipment.serial_number == serial_number)
        )

    def list_filtered(
        self,
        location_id: Optional[uuid.UUID] = None,
        category: Optional[EquipmentCategory] = None,
        status: Optional[EquipmentStatus] = EquipmentStatus.active,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Equipment], int]:
        query = select(Equipment)
        if location_id is not None:
            query = query.where(Equipment.location_id == location_id)
        if category is not None:
            query = query.where(Equipment.category == category)
        if status is not None:
            query = query.where(Equipment.status == status)

        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            self.db.scalars(
                query.order_by(Equipment.name)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def list_for_export(
        self,
        location_id: Optional[uuid.UUID] = None,
        category: Optional[EquipmentCategory] = None,
        status: Optional[EquipmentStatus] = None,
    ) -> list[Equipment]:
        query = select(Equipment)
        if location_id is not None:
            query = query.where(Equipment.location_id == location_id)
        if category is not None:
            query = query.where(Equipment.category == category)
        if status is not None:
            query = query.where(Equipment.status == status)
        return list(self.db.scalars(query.order_by(Equipment.name)))

    def list_active_for_location(self, location_id: uuid.UUID) -> list[Equipment]:
        return list(
            self.db.scalars(
                select(Equipment)
                .where(
                    Equipment.location_id == location_id,
                    Equipment.status == EquipmentStatus.active,
                )
                .order_by(Equipment.name)
            )
        )

    def retire(
        self, equipment: Equipment, retired_by_id: uuid.UUID, reason: str
    ) -> Equipment:
        equipment.status = EquipmentStatus.retired
        equipment.retired_at = datetime.now(timezone.utc)
        equipment.retired_by_id = retired_by_id
        equipment.retirement_reason = reason
        self.db.commit()
        self.db.refresh(equipment)
        return equipment
