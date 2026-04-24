import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.equipment import Equipment, EquipmentStatus
from app.models.location import Location
from app.repositories.base import BaseRepository


class LocationRepository(BaseRepository[Location]):
    def __init__(self, db: Session) -> None:
        super().__init__(Location, db)

    def get_by_name(self, name: str) -> Optional[Location]:
        return self.db.scalar(select(Location).where(Location.name == name))

    def list_all(self) -> list[Location]:
        return list(self.db.scalars(select(Location).order_by(Location.name)))

    def get_active_equipment_count(self, location_id: uuid.UUID) -> int:
        return self.db.scalar(
            select(func.count(Equipment.id)).where(
                Equipment.location_id == location_id,
                Equipment.status == EquipmentStatus.active,
            )
        ) or 0

    def has_any_equipment(self, location_id: uuid.UUID) -> bool:
        return (
            self.db.scalar(
                select(func.count(Equipment.id)).where(
                    Equipment.location_id == location_id,
                    Equipment.status == EquipmentStatus.active,
                )
            )
            or 0
        ) > 0
