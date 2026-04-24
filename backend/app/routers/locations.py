import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.models.user import User
from app.schemas.location import (
    Location,
    LocationCreateRequest,
    LocationDetail,
    LocationListResponse,
    LocationUpdateRequest,
)
from app.services import location_service

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=LocationListResponse)
def list_locations(
    _: Annotated[User, Depends(require_permission("locations:read"))],
    db: Session = Depends(get_db),
):
    items = location_service.list_all(db)
    return LocationListResponse(items=items, total=len(items))


@router.post("", response_model=Location, status_code=201)
def create_location(
    body: LocationCreateRequest,
    _: Annotated[User, Depends(require_permission("locations:write"))],
    db: Session = Depends(get_db),
):
    return location_service.create(body, db)


@router.get("/{location_id}", response_model=LocationDetail)
def get_location(
    location_id: uuid.UUID,
    _: Annotated[User, Depends(require_permission("locations:read"))],
    db: Session = Depends(get_db),
):
    return location_service.get_detail(location_id, db)


@router.put("/{location_id}", response_model=Location)
def update_location(
    location_id: uuid.UUID,
    body: LocationUpdateRequest,
    _: Annotated[User, Depends(require_permission("locations:write"))],
    db: Session = Depends(get_db),
):
    return location_service.update(location_id, body, db)


@router.delete("/{location_id}", status_code=204)
def delete_location(
    location_id: uuid.UUID,
    _: Annotated[User, Depends(require_permission("locations:write"))],
    db: Session = Depends(get_db),
):
    location_service.delete(location_id, db)
