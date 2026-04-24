import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_item import AuditItem, CheckMethod
from app.models.audit_session import AuditSession, AuditSessionStatus
from app.models.equipment import Equipment
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditSession]):
    def __init__(self, db: Session) -> None:
        super().__init__(AuditSession, db)

    def get_open_session_for_location(
        self, location_id: uuid.UUID
    ) -> Optional[AuditSession]:
        return self.db.scalar(
            select(AuditSession).where(
                AuditSession.location_id == location_id,
                AuditSession.status == AuditSessionStatus.in_progress,
            )
        )

    def list_filtered(
        self,
        location_id: Optional[uuid.UUID] = None,
        status: Optional[AuditSessionStatus] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditSession], int]:
        from sqlalchemy import func

        query = select(AuditSession)
        if location_id is not None:
            query = query.where(AuditSession.location_id == location_id)
        if status is not None:
            query = query.where(AuditSession.status == status)

        from sqlalchemy import select as _select
        total = (
            self.db.scalar(
                _select(func.count()).select_from(query.subquery())
            )
            or 0
        )
        items = list(
            self.db.scalars(
                query.order_by(AuditSession.started_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def bulk_create_items(
        self, session_id: uuid.UUID, equipment_list: list[Equipment]
    ) -> list[AuditItem]:
        items = [
            AuditItem(audit_session_id=session_id, equipment_id=e.id)
            for e in equipment_list
        ]
        self.db.add_all(items)
        self.db.commit()
        for item in items:
            self.db.refresh(item)
        return items

    def get_item_by_equipment(
        self, session_id: uuid.UUID, equipment_id: uuid.UUID
    ) -> Optional[AuditItem]:
        return self.db.scalar(
            select(AuditItem).where(
                AuditItem.audit_session_id == session_id,
                AuditItem.equipment_id == equipment_id,
            )
        )

    def get_item_by_qr_code(
        self, session_id: uuid.UUID, qr_code: str
    ) -> Optional[AuditItem]:
        return self.db.scalar(
            select(AuditItem)
            .join(Equipment, AuditItem.equipment_id == Equipment.id)
            .where(
                AuditItem.audit_session_id == session_id,
                Equipment.qr_code == qr_code,
            )
        )

    def mark_item(
        self,
        item: AuditItem,
        is_present: bool,
        method: CheckMethod,
    ) -> AuditItem:
        item.is_present = is_present
        item.check_method = method
        item.checked_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(item)
        return item

    def complete_session(self, session: AuditSession) -> AuditSession:
        session.status = AuditSessionStatus.completed
        session.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_items(self, session_id: uuid.UUID) -> list[AuditItem]:
        return list(
            self.db.scalars(
                select(AuditItem)
                .where(AuditItem.audit_session_id == session_id)
                .join(Equipment)
                .order_by(Equipment.name)
            )
        )
