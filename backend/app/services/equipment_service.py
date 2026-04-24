import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.equipment import Equipment
from app.repositories.equipment_repo import EquipmentRepository
from app.repositories.location_repo import LocationRepository
from app.schemas.equipment import (
    EquipmentCreateRequest,
    EquipmentListQuery,
    EquipmentListResponse,
    EquipmentUpdateRequest,
)


def _assert_location_exists(location_id: uuid.UUID, db: Session) -> None:
    if LocationRepository(db).get(location_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"code": "LOCATION_NOT_FOUND", "message": "Location not found"})


def get_or_404(equipment_id: uuid.UUID, db: Session) -> Equipment:
    eq = EquipmentRepository(db).get(equipment_id)
    if eq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"code": "EQUIPMENT_NOT_FOUND", "message": "Equipment not found"})
    return eq


def list_equipment(query: EquipmentListQuery, db: Session) -> EquipmentListResponse:
    repo = EquipmentRepository(db)
    items, total = repo.list_filtered(
        location_id=query.location_id,
        category=query.category,
        status=query.status,
        page=query.page,
        page_size=query.page_size,
    )
    return EquipmentListResponse(items=items, total=total, page=query.page, page_size=query.page_size)


def create(body: EquipmentCreateRequest, created_by_id: uuid.UUID, db: Session) -> Equipment:
    _assert_location_exists(body.location_id, db)
    repo = EquipmentRepository(db)

    if body.serial_number and repo.get_by_serial_number(body.serial_number):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail={"code": "DUPLICATE_SERIAL_NUMBER",
                                    "message": "Serial number already exists"})

    qr_code = f"halo-inv://{uuid.uuid4()}"
    eq = Equipment(
        id=uuid.uuid4(),
        name=body.name,
        category=body.category,
        location_id=body.location_id,
        manufacturer=body.manufacturer,
        model=body.model,
        serial_number=body.serial_number,
        room=body.room,
        assigned_to=body.assigned_to,
        qr_code=qr_code,
        created_by_id=created_by_id,
    )
    return repo.save(eq)


def update(equipment_id: uuid.UUID, body: EquipmentUpdateRequest, db: Session) -> Equipment:
    repo = EquipmentRepository(db)
    eq = get_or_404(equipment_id, db)

    if body.location_id is not None and body.location_id != eq.location_id:
        _assert_location_exists(body.location_id, db)
        eq.location_id = body.location_id
    if body.serial_number is not None and body.serial_number != eq.serial_number:
        existing = repo.get_by_serial_number(body.serial_number)
        if existing and existing.id != equipment_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail={"code": "DUPLICATE_SERIAL_NUMBER",
                                        "message": "Serial number already exists"})
        eq.serial_number = body.serial_number
    if body.name is not None:
        eq.name = body.name
    if body.category is not None:
        eq.category = body.category
    if body.manufacturer is not None:
        eq.manufacturer = body.manufacturer
    if body.model is not None:
        eq.model = body.model
    if body.room is not None:
        eq.room = body.room
    if body.assigned_to is not None:
        eq.assigned_to = body.assigned_to
    return repo.save(eq)
