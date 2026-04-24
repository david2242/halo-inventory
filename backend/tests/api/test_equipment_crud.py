import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models as _models  # noqa: F401
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.base import Base
from app.models.equipment import Equipment, EquipmentCategory, EquipmentStatus
from app.models.location import Location
from app.models.user import User, UserRole


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def set_pragma(conn, _):
        conn.cursor().execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    def override():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    db = SessionLocal()
    yield db
    db.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(test_db):
    return TestClient(app)


@pytest.fixture
def director(test_db: Session) -> User:
    user = User(id=uuid.uuid4(), email="d@test.hu", full_name="D", role=UserRole.director,
                password_hash=hash_password("pass1234"), is_active=True)
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def auth_headers(client, director):
    r = client.post("/api/v1/auth/login", json={"email": "d@test.hu", "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def location(test_db: Session) -> Location:
    loc = Location(id=uuid.uuid4(), name="Teszt Telephely")
    test_db.add(loc)
    test_db.commit()
    return loc


def make_eq(location_id, created_by_id, name="Laptop 1", sn=None):
    return Equipment(id=uuid.uuid4(), name=name, category=EquipmentCategory.laptop,
                     qr_code=f"halo-inv://{uuid.uuid4()}", location_id=location_id,
                     created_by_id=created_by_id, status=EquipmentStatus.active,
                     serial_number=sn)


# --- CRUD ---

def test_create_equipment(client, auth_headers, location):
    resp = client.post("/api/v1/equipment", json={
        "name": "Dell Laptop", "category": "laptop", "location_id": str(location.id)
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Dell Laptop"
    assert data["qr_code"].startswith("halo-inv://")
    assert data["status"] == "active"


def test_create_equipment_duplicate_serial(client, auth_headers, location, test_db, director):
    test_db.add(make_eq(location.id, director.id, sn="SN-001"))
    test_db.commit()
    resp = client.post("/api/v1/equipment", json={
        "name": "Another", "category": "laptop",
        "location_id": str(location.id), "serial_number": "SN-001"
    }, headers=auth_headers)
    assert resp.status_code == 409


def test_list_equipment_filter_location(client, auth_headers, location, test_db, director):
    loc2 = Location(id=uuid.uuid4(), name="Másik")
    test_db.add(loc2)
    test_db.add(make_eq(location.id, director.id, name="Here"))
    test_db.add(make_eq(loc2.id, director.id, name="There"))
    test_db.commit()

    resp = client.get(f"/api/v1/equipment?location_id={location.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["name"] == "Here"


def test_list_equipment_filter_status(client, auth_headers, location, test_db, director):
    active = make_eq(location.id, director.id, name="Active")
    retired = make_eq(location.id, director.id, name="Retired")
    retired.status = EquipmentStatus.retired
    test_db.add_all([active, retired])
    test_db.commit()

    resp = client.get("/api/v1/equipment?status=retired", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["name"] == "Retired"


def test_get_equipment(client, auth_headers, location, test_db, director):
    eq = make_eq(location.id, director.id)
    test_db.add(eq)
    test_db.commit()
    resp = client.get(f"/api/v1/equipment/{eq.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == str(eq.id)


def test_update_equipment_partial(client, auth_headers, location, test_db, director):
    eq = make_eq(location.id, director.id, name="Original")
    test_db.add(eq)
    test_db.commit()
    resp = client.put(f"/api/v1/equipment/{eq.id}", json={"name": "Updated"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"
    assert resp.json()["category"] == "laptop"  # unchanged


def test_equipment_requires_auth(client):
    resp = client.get("/api/v1/equipment")
    assert resp.status_code in (401, 403)
