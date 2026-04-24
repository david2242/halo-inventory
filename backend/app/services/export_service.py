import io
from typing import Optional

from sqlalchemy.orm import Session

from app.models.equipment import Equipment


def export_equipment_xlsx(items: list[Equipment], db: Session) -> bytes:
    import openpyxl
    from openpyxl.styles import Font

    from app.repositories.location_repo import LocationRepository

    location_cache: dict = {}

    def get_location_name(location_id) -> str:
        if location_id not in location_cache:
            loc = LocationRepository(db).get(location_id)
            location_cache[location_id] = loc.name if loc else ""
        return location_cache[location_id]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Eszközök"

    headers = [
        "Név", "Kategória", "Gyártó", "Modell", "Sorozatszám",
        "Telephely", "Szoba", "Felelős", "Státusz",
        "Selejtezés oka", "Selejtezés dátuma", "Létrehozva",
    ]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for eq in items:
        ws.append([
            eq.name,
            eq.category.value,
            eq.manufacturer or "",
            eq.model or "",
            eq.serial_number or "",
            get_location_name(eq.location_id),
            eq.room or "",
            eq.assigned_to or "",
            eq.status.value,
            eq.retirement_reason or "",
            eq.retired_at.isoformat() if eq.retired_at else "",
            eq.created_at.isoformat() if eq.created_at else "",
        ])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
