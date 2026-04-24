import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.audit_item import CheckMethod
from app.models.audit_session import AuditSessionStatus
from app.models.equipment import Equipment, EquipmentCategory, EquipmentStatus
from app.models.location import Location
from app.models.user import User
from app.repositories import (
    AuditRepository,
    EquipmentRepository,
    LocationRepository,
    UserRepository,
)


def make_equipment(location_id, created_by_id, **kwargs) -> Equipment:
    defaults = dict(
        id=uuid.uuid4(),
        name="Laptop 1",
        category=EquipmentCategory.laptop,
        qr_code=f"halo-inv://{uuid.uuid4()}",
        location_id=location_id,
        created_by_id=created_by_id,
        status=EquipmentStatus.active,
    )
    defaults.update(kwargs)
    return Equipment(**defaults)


# --- LocationRepository ---

def test_location_list_all_ordered(db: Session, location: Location):
    loc2 = Location(id=uuid.uuid4(), name="Aaa Telephely")
    db.add(loc2)
    db.commit()

    repo = LocationRepository(db)
    result = repo.list_all()
    assert result[0].name == "Aaa Telephely"
    assert result[1].name == "Teszt Telephely"


def test_location_get_by_name(db: Session, location: Location):
    repo = LocationRepository(db)
    found = repo.get_by_name("Teszt Telephely")
    assert found is not None
    assert found.id == location.id

    not_found = repo.get_by_name("Nem Létező")
    assert not_found is None


def test_location_has_any_equipment(db: Session, location: Location, director_user: User):
    repo = LocationRepository(db)
    assert not repo.has_any_equipment(location.id)

    eq = make_equipment(location.id, director_user.id)
    db.add(eq)
    db.commit()

    assert repo.has_any_equipment(location.id)


# --- EquipmentRepository ---

def test_equipment_get_by_qr_code(db: Session, location: Location, director_user: User):
    qr = f"halo-inv://{uuid.uuid4()}"
    eq = make_equipment(location.id, director_user.id, qr_code=qr)
    db.add(eq)
    db.commit()

    repo = EquipmentRepository(db)
    found = repo.get_by_qr_code(qr)
    assert found is not None
    assert found.id == eq.id

    not_found = repo.get_by_qr_code("halo-inv://unknown")
    assert not_found is None


def test_equipment_list_filtered_by_location(db: Session, location: Location, director_user: User):
    loc2 = Location(id=uuid.uuid4(), name="Másik Telephely")
    db.add(loc2)
    eq1 = make_equipment(location.id, director_user.id, name="Eszköz A")
    eq2 = make_equipment(loc2.id, director_user.id, name="Eszköz B")
    db.add_all([eq1, eq2])
    db.commit()

    repo = EquipmentRepository(db)
    items, total = repo.list_filtered(location_id=location.id)
    assert total == 1
    assert items[0].name == "Eszköz A"


def test_equipment_list_filtered_by_status(db: Session, location: Location, director_user: User):
    active = make_equipment(location.id, director_user.id, name="Aktív")
    retired = make_equipment(
        location.id, director_user.id,
        name="Selejtezett",
        status=EquipmentStatus.retired,
        qr_code=f"halo-inv://{uuid.uuid4()}"
    )
    db.add_all([active, retired])
    db.commit()

    repo = EquipmentRepository(db)
    items, total = repo.list_filtered(status=EquipmentStatus.retired)
    assert total == 1
    assert items[0].name == "Selejtezett"


def test_equipment_list_filtered_by_category(db: Session, location: Location, director_user: User):
    laptop = make_equipment(location.id, director_user.id, name="Laptop", category=EquipmentCategory.laptop)
    printer = make_equipment(location.id, director_user.id, name="Nyomtató",
                             category=EquipmentCategory.printer, qr_code=f"halo-inv://{uuid.uuid4()}")
    db.add_all([laptop, printer])
    db.commit()

    repo = EquipmentRepository(db)
    items, total = repo.list_filtered(category=EquipmentCategory.printer)
    assert total == 1
    assert items[0].name == "Nyomtató"


def test_equipment_retire(db: Session, location: Location, director_user: User):
    eq = make_equipment(location.id, director_user.id)
    db.add(eq)
    db.commit()

    repo = EquipmentRepository(db)
    retired = repo.retire(eq, director_user.id, "Elromlott")

    assert retired.status == EquipmentStatus.retired
    assert retired.retirement_reason == "Elromlott"
    assert retired.retired_by_id == director_user.id
    assert retired.retired_at is not None

    # Verify it's actually in the DB as retired, not deleted
    db.expire_all()
    same = db.get(Equipment, eq.id)
    assert same is not None
    assert same.status == EquipmentStatus.retired


# --- AuditRepository ---

def test_audit_get_open_session_none(db: Session, location: Location):
    repo = AuditRepository(db)
    result = repo.get_open_session_for_location(location.id)
    assert result is None


def test_audit_bulk_create_items(db: Session, location: Location, director_user: User):
    from app.models.audit_session import AuditSession
    session = AuditSession(
        id=uuid.uuid4(),
        location_id=location.id,
        started_by_id=director_user.id,
    )
    db.add(session)

    eq1 = make_equipment(location.id, director_user.id, name="E1")
    eq2 = make_equipment(location.id, director_user.id, name="E2",
                         qr_code=f"halo-inv://{uuid.uuid4()}")
    db.add_all([eq1, eq2])
    db.commit()

    repo = AuditRepository(db)
    items = repo.bulk_create_items(session.id, [eq1, eq2])
    db.commit()

    assert len(items) == 2
    for item in items:
        assert item.is_present is None
        assert item.check_method is None


def test_audit_mark_item(db: Session, location: Location, director_user: User):
    from app.models.audit_session import AuditSession
    session = AuditSession(
        id=uuid.uuid4(),
        location_id=location.id,
        started_by_id=director_user.id,
    )
    db.add(session)
    eq = make_equipment(location.id, director_user.id)
    db.add(eq)
    db.commit()

    repo = AuditRepository(db)
    items = repo.bulk_create_items(session.id, [eq])
    db.commit()

    marked = repo.mark_item(items[0], is_present=True, method=CheckMethod.scan)
    db.commit()

    assert marked.is_present is True
    assert marked.check_method == CheckMethod.scan
    assert marked.checked_at is not None
