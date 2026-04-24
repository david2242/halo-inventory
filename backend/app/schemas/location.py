import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LocationBase(BaseModel):
    name: str
    address: Optional[str] = None


class LocationCreateRequest(LocationBase):
    pass


class LocationUpdateRequest(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None


class Location(LocationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LocationDetail(Location):
    equipment_count: int


class LocationListResponse(BaseModel):
    items: list[Location]
    total: int
