import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.models.equipment import EquipmentCategory, EquipmentStatus
from app.models.user import User
from app.schemas.equipment import (
    Equipment,
    EquipmentCreateRequest,
    EquipmentListQuery,
    EquipmentListResponse,
    EquipmentUpdateRequest,
    RetireRequest,
)
from app.services import equipment_service

router = APIRouter(prefix="/equipment", tags=["equipment"])


# NOTE: /export MUST be registered before /{equipment_id} to avoid route conflict (D-001 gap)
@router.get("/export")
def export_equipment(
    _: Annotated[User, Depends(require_permission("equipment:export"))],
    location_id: uuid.UUID | None = Query(default=None),
    category: EquipmentCategory | None = Query(default=None),
    status: EquipmentStatus | None = Query(default=None),
    db: Session = Depends(get_db),
):
    from app.services.export_service import export_equipment_xlsx
    from fastapi.responses import StreamingResponse
    import io

    from app.repositories.equipment_repo import EquipmentRepository
    items = EquipmentRepository(db).list_for_export(
        location_id=location_id, category=category, status=status
    )
    output = export_equipment_xlsx(items, db)
    return StreamingResponse(
        io.BytesIO(output),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=equipment_export.xlsx"},
    )


@router.get("", response_model=EquipmentListResponse)
def list_equipment(
    _: Annotated[User, Depends(require_permission("equipment:read"))],
    location_id: uuid.UUID | None = Query(default=None),
    category: EquipmentCategory | None = Query(default=None),
    status: EquipmentStatus | None = Query(default=EquipmentStatus.active),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = EquipmentListQuery(
        location_id=location_id, category=category, status=status,
        page=page, page_size=page_size,
    )
    return equipment_service.list_equipment(query, db)


@router.post("", response_model=Equipment, status_code=201)
def create_equipment(
    body: EquipmentCreateRequest,
    current_user: Annotated[User, Depends(require_permission("equipment:write"))],
    db: Session = Depends(get_db),
):
    return equipment_service.create(body, current_user.id, db)


@router.get("/{equipment_id}", response_model=Equipment)
def get_equipment(
    equipment_id: uuid.UUID,
    _: Annotated[User, Depends(require_permission("equipment:read"))],
    db: Session = Depends(get_db),
):
    return equipment_service.get_or_404(equipment_id, db)


@router.put("/{equipment_id}", response_model=Equipment)
def update_equipment(
    equipment_id: uuid.UUID,
    body: EquipmentUpdateRequest,
    _: Annotated[User, Depends(require_permission("equipment:write"))],
    db: Session = Depends(get_db),
):
    return equipment_service.update(equipment_id, body, db)


@router.post("/{equipment_id}/retire", response_model=Equipment)
def retire_equipment(
    equipment_id: uuid.UUID,
    body: RetireRequest,
    current_user: Annotated[User, Depends(require_permission("equipment:retire"))],
    db: Session = Depends(get_db),
):
    from app.services.equipment_actions_service import retire
    return retire(equipment_id, body.reason, current_user.id, db)


@router.get("/{equipment_id}/qr")
def get_qr(
    equipment_id: uuid.UUID,
    _: Annotated[User, Depends(require_permission("equipment:read"))],
    db: Session = Depends(get_db),
):
    from app.services.qr_service import generate_qr_png
    from fastapi.responses import Response
    eq = equipment_service.get_or_404(equipment_id, db)
    png_bytes = generate_qr_png(eq, db)
    return Response(content=png_bytes, media_type="image/png")
