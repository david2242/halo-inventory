import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.equipment import EquipmentCategory, EquipmentStatus


class EquipmentCreateRequest(BaseModel):
    name: str
    category: EquipmentCategory
    location_id: uuid.UUID
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    room: Optional[str] = None
    assigned_to: Optional[str] = None


class EquipmentUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[EquipmentCategory] = None
    location_id: Optional[uuid.UUID] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    room: Optional[str] = None
    assigned_to: Optional[str] = None


class RetireRequest(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_min_length(cls, v: str) -> str:
        if len(v.strip()) < 5:
            raise ValueError("Retirement reason must be at least 5 characters")
        return v


class EquipmentListQuery(BaseModel):
    location_id: Optional[uuid.UUID] = None
    category: Optional[EquipmentCategory] = None
    status: Optional[EquipmentStatus] = EquipmentStatus.active
    page: int = 1
    page_size: int = 50

    @field_validator("page_size")
    @classmethod
    def page_size_max(cls, v: int) -> int:
        if v > 200:
            raise ValueError("page_size cannot exceed 200")
        return v


class EquipmentExportQuery(BaseModel):
    location_id: Optional[uuid.UUID] = None
    category: Optional[EquipmentCategory] = None
    status: Optional[EquipmentStatus] = None


class Equipment(BaseModel):
    id: uuid.UUID
    name: str
    category: EquipmentCategory
    manufacturer: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    qr_code: str
    location_id: uuid.UUID
    room: Optional[str]
    assigned_to: Optional[str]
    status: EquipmentStatus
    retired_at: Optional[datetime]
    retired_by_id: Optional[uuid.UUID]
    retirement_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by_id: uuid.UUID

    model_config = {"from_attributes": True}


class EquipmentListResponse(BaseModel):
    items: list[Equipment]
    total: int
    page: int
    page_size: int
