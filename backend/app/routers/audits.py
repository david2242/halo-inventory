import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.models.audit_session import AuditSessionStatus
from app.models.user import User
from app.schemas.audit import (
    AuditDetail,
    AuditItem,
    AuditListResponse,
    AuditReport,
    AuditSession,
    AuditStartRequest,
    ManualCheckRequest,
    ScanRequest,
)
from app.services import audit_service

router = APIRouter(prefix="/audits", tags=["audits"])


@router.post("", response_model=AuditSession, status_code=201)
def start_audit(
    body: AuditStartRequest,
    current_user: Annotated[User, Depends(require_permission("audits:write"))],
    db: Session = Depends(get_db),
):
    return audit_service.start_session(body, current_user, db)


@router.get("", response_model=AuditListResponse)
def list_audits(
    _: Annotated[User, Depends(require_permission("audits:read"))],
    location_id: Optional[uuid.UUID] = Query(default=None),
    status: Optional[AuditSessionStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return audit_service.list_sessions(location_id, status, page, page_size, db)


@router.get("/{session_id}", response_model=AuditDetail)
def get_audit(
    session_id: uuid.UUID,
    _: Annotated[User, Depends(require_permission("audits:read"))],
    db: Session = Depends(get_db),
):
    return audit_service.get_detail(session_id, db)


@router.post("/{session_id}/scan", response_model=AuditItem)
def scan_item(
    session_id: uuid.UUID,
    body: ScanRequest,
    _: Annotated[User, Depends(require_permission("audits:write"))],
    db: Session = Depends(get_db),
):
    return audit_service.scan_item(session_id, body.qr_code, db)


@router.post("/{session_id}/manual", response_model=AuditItem)
def manual_check(
    session_id: uuid.UUID,
    body: ManualCheckRequest,
    _: Annotated[User, Depends(require_permission("audits:write"))],
    db: Session = Depends(get_db),
):
    return audit_service.manual_check(session_id, body.equipment_id, body.is_present, db)


@router.post("/{session_id}/complete", response_model=AuditSession)
def complete_audit(
    session_id: uuid.UUID,
    _: Annotated[User, Depends(require_permission("audits:write"))],
    db: Session = Depends(get_db),
):
    return audit_service.complete_session(session_id, db)


@router.get("/{session_id}/report", response_model=AuditReport)
def get_report(
    session_id: uuid.UUID,
    _: Annotated[User, Depends(require_permission("audits:read"))],
    db: Session = Depends(get_db),
):
    return audit_service.get_report(session_id, db)
