import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.audit_item import AuditItem, CheckMethod
from app.models.audit_session import AuditSession, AuditSessionStatus
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.equipment_repo import EquipmentRepository
from app.repositories.location_repo import LocationRepository
from app.schemas.audit import (
    AuditDetail,
    AuditListResponse,
    AuditReport,
    AuditStartRequest,
    AuditSummary,
)


def start_session(data: AuditStartRequest, current_user: User, db: Session) -> AuditSession:
    location_repo = LocationRepository(db)
    location = location_repo.get(data.location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    audit_repo = AuditRepository(db)
    if audit_repo.get_open_session_for_location(data.location_id):
        raise HTTPException(status_code=409, detail="An audit session is already in progress for this location")

    session = AuditSession(
        id=uuid.uuid4(),
        location_id=data.location_id,
        started_by_id=current_user.id,
        status=AuditSessionStatus.in_progress,
        notes=data.notes,
    )
    audit_repo.save(session)

    equipment_list = EquipmentRepository(db).list_active_for_location(data.location_id)
    if equipment_list:
        audit_repo.bulk_create_items(session.id, equipment_list)

    db.refresh(session)
    return session


def list_sessions(
    location_id, status, page: int, page_size: int, db: Session
) -> AuditListResponse:
    items, total = AuditRepository(db).list_filtered(
        location_id=location_id, status=status, page=page, page_size=page_size
    )
    return AuditListResponse(items=items, total=total)


def get_session_or_404(session_id: uuid.UUID, db: Session) -> AuditSession:
    session = AuditRepository(db).get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found")
    return session


def get_detail(session_id: uuid.UUID, db: Session) -> AuditDetail:
    session = get_session_or_404(session_id, db)
    repo = AuditRepository(db)
    items = repo.get_session_items(session_id)
    summary = _build_summary(items)
    return AuditDetail(session=session, summary=summary, items=items)


def scan_item(session_id: uuid.UUID, qr_code: str, db: Session) -> AuditItem:
    session = get_session_or_404(session_id, db)
    _assert_in_progress(session)

    repo = AuditRepository(db)
    item = repo.get_item_by_qr_code(session_id, qr_code)
    if not item:
        raise HTTPException(status_code=404, detail="Equipment with this QR code not found in session")
    return repo.mark_item(item, is_present=True, method=CheckMethod.scan)


def manual_check(session_id: uuid.UUID, equipment_id: uuid.UUID, is_present: bool, db: Session) -> AuditItem:
    session = get_session_or_404(session_id, db)
    _assert_in_progress(session)

    repo = AuditRepository(db)
    item = repo.get_item_by_equipment(session_id, equipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Equipment not found in this audit session")
    return repo.mark_item(item, is_present=is_present, method=CheckMethod.manual)


def complete_session(session_id: uuid.UUID, db: Session) -> AuditSession:
    repo = AuditRepository(db)
    session = get_session_or_404(session_id, db)
    _assert_in_progress(session)
    return repo.complete_session(session)


def get_report(session_id: uuid.UUID, db: Session) -> AuditReport:
    session = get_session_or_404(session_id, db)
    repo = AuditRepository(db)
    items = repo.get_session_items(session_id)
    summary = _build_summary(items)

    present = [i.equipment for i in items if i.is_present is True]
    missing = [i.equipment for i in items if i.is_present is False]
    unchecked = [i.equipment for i in items if i.is_present is None]

    from app.repositories.user_repo import UserRepository
    auditor = UserRepository(db).get(session.started_by_id)

    return AuditReport(
        session=session,
        location_id=session.location_id,
        auditor_id=session.started_by_id,
        auditor_name=auditor.full_name if auditor else "Unknown",
        summary=summary,
        present_items=present,
        missing_items=missing,
        unchecked_items=unchecked,
    )


def _assert_in_progress(session: AuditSession) -> None:
    if session.status != AuditSessionStatus.in_progress:
        raise HTTPException(status_code=409, detail="Audit session is already completed")


def _build_summary(items) -> AuditSummary:
    present = sum(1 for i in items if i.is_present is True)
    missing = sum(1 for i in items if i.is_present is False)
    unchecked = sum(1 for i in items if i.is_present is None)
    return AuditSummary(total=len(items), present=present, missing=missing, unchecked=unchecked)
