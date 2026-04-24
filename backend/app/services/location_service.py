import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.location import Location
from app.repositories.location_repo import LocationRepository
from app.schemas.location import LocationCreateRequest, LocationDetail, LocationUpdateRequest


def list_all(db: Session) -> list[Location]:
    return LocationRepository(db).list_all()


def get_or_404(location_id: uuid.UUID, db: Session) -> Location:
    loc = LocationRepository(db).get(location_id)
    if loc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"code": "LOCATION_NOT_FOUND", "message": "Location not found"})
    return loc


def get_detail(location_id: uuid.UUID, db: Session) -> LocationDetail:
    repo = LocationRepository(db)
    loc = repo.get(location_id)
    if loc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"code": "LOCATION_NOT_FOUND", "message": "Location not found"})
    count = repo.get_active_equipment_count(location_id)
    return LocationDetail.model_validate({**loc.__dict__, "equipment_count": count})


def create(body: LocationCreateRequest, db: Session) -> Location:
    repo = LocationRepository(db)
    if repo.get_by_name(body.name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail={"code": "DUPLICATE_LOCATION_NAME", "message": "Location name already exists"})
    loc = Location(id=uuid.uuid4(), name=body.name, address=body.address)
    return repo.save(loc)


def update(location_id: uuid.UUID, body: LocationUpdateRequest, db: Session) -> Location:
    repo = LocationRepository(db)
    loc = get_or_404(location_id, db)
    if body.name is not None and body.name != loc.name:
        if repo.get_by_name(body.name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail={"code": "DUPLICATE_LOCATION_NAME", "message": "Location name already exists"})
        loc.name = body.name
    if body.address is not None:
        loc.address = body.address
    return repo.save(loc)


def delete(location_id: uuid.UUID, db: Session) -> None:
    repo = LocationRepository(db)
    loc = get_or_404(location_id, db)
    if repo.has_any_equipment(location_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail={"code": "LOCATION_HAS_EQUIPMENT",
                                    "message": "Cannot delete location with active equipment"})
    repo.delete(loc)
