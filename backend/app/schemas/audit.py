import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.audit_item import CheckMethod
from app.models.audit_session import AuditSessionStatus
from app.schemas.equipment import Equipment


class AuditStartRequest(BaseModel):
    location_id: uuid.UUID
    notes: Optional[str] = None


class AuditSession(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    started_by_id: uuid.UUID
    started_at: datetime
    completed_at: Optional[datetime]
    status: AuditSessionStatus
    notes: Optional[str]

    model_config = {"from_attributes": True}


class AuditSessionResponse(AuditSession):
    item_count: int


class AuditListQuery(BaseModel):
    location_id: Optional[uuid.UUID] = None
    status: Optional[AuditSessionStatus] = None
    page: int = 1
    page_size: int = 50


class AuditListResponse(BaseModel):
    items: list[AuditSession]
    total: int


class AuditItem(BaseModel):
    id: uuid.UUID
    audit_session_id: uuid.UUID
    equipment_id: uuid.UUID
    check_method: Optional[CheckMethod]
    checked_at: Optional[datetime]
    is_present: Optional[bool]

    model_config = {"from_attributes": True}


class AuditItemWithEquipment(AuditItem):
    equipment: Equipment


class AuditSummary(BaseModel):
    total: int
    present: int
    missing: int
    unchecked: int


class AuditDetail(BaseModel):
    session: AuditSession
    summary: AuditSummary
    items: list[AuditItemWithEquipment]


class ScanRequest(BaseModel):
    qr_code: str


class ManualCheckRequest(BaseModel):
    equipment_id: uuid.UUID
    is_present: bool


class ReportQuery(BaseModel):
    format: str = "json"


class AuditReport(BaseModel):
    session: AuditSession
    location_id: uuid.UUID
    auditor_id: uuid.UUID
    auditor_name: str
    summary: AuditSummary
    present_items: list[Equipment]
    missing_items: list[Equipment]
    unchecked_items: list[Equipment]
