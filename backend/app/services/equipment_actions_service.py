import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.equipment import Equipment, EquipmentStatus
from app.repositories.equipment_repo import EquipmentRepository


def retire(equipment_id: uuid.UUID, reason: str, retired_by_id: uuid.UUID, db: Session) -> Equipment:
    repo = EquipmentRepository(db)
    eq = repo.get(equipment_id)
    if eq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"code": "EQUIPMENT_NOT_FOUND", "message": "Equipment not found"})
    if eq.status == EquipmentStatus.retired:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail={"code": "EQUIPMENT_ALREADY_RETIRED", "message": "Equipment is already retired"})
    return repo.retire(eq, retired_by_id, reason)
