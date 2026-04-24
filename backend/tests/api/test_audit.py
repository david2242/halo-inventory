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
from app.models.audit_session import AuditSession, AuditSessionStatus
from app.models.base import Base
from app.models.equipment import Equipment, EquipmentCategory, EquipmentStatus
from app.models.location import Location
from app.models.user import User, UserRole


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

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
    user = User(
        id=uuid.uuid4(), email="d@test.hu", full_name="D",
        role=UserRole.director, password_hash=hash_password("pass1234"), is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def auth_headers(client, director):
    r = client.post("/api/v1/auth/login", json={"email": "d@test.hu", "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def location(test_db: Session) -> Location:
    loc = Location(id=uuid.uuid4(), name="Telephely A")
    test_db.add(loc)
    test_db.commit()
    return loc


@pytest.fixture
def equipment_item(test_db: Session, location: Location, director: User) -> Equipment:
    eq = Equipment(
        id=uuid.uuid4(), name="Laptop 1", category=EquipmentCategory.laptop,
        qr_code=f"halo-inv://{uuid.uuid4()}", location_id=location.id,
        created_by_id=director.id, status=EquipmentStatus.active,
    )
    test_db.add(eq)
    test_db.commit()
    return eq


def test_start_audit(client, auth_headers, location, equipment_item):
    resp = client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "in_progress"
    assert data["location_id"] == str(location.id)


def test_start_audit_duplicate(client, auth_headers, location, equipment_item):
    client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    resp = client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    assert resp.status_code == 409


def test_start_audit_unknown_location(client, auth_headers):
    resp = client.post("/api/v1/audits", json={"location_id": str(uuid.uuid4())}, headers=auth_headers)
    assert resp.status_code == 404


def test_list_audits(client, auth_headers, location, equipment_item):
    client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    resp = client.get("/api/v1/audits", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_get_audit_detail(client, auth_headers, location, equipment_item):
    r = client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    session_id = r.json()["id"]

    resp = client.get(f"/api/v1/audits/{session_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total"] == 1
    assert data["summary"]["unchecked"] == 1
    assert len(data["items"]) == 1


def test_scan_item(client, auth_headers, location, equipment_item):
    r = client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    session_id = r.json()["id"]

    resp = client.post(
        f"/api/v1/audits/{session_id}/scan",
        json={"qr_code": equipment_item.qr_code},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_present"] is True
    assert resp.json()["check_method"] == "scan"


def test_scan_unknown_qr(client, auth_headers, location, equipment_item):
    r = client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    session_id = r.json()["id"]

    resp = client.post(
        f"/api/v1/audits/{session_id}/scan",
        json={"qr_code": "halo-inv://unknown"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_manual_check(client, auth_headers, location, equipment_item):
    r = client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    session_id = r.json()["id"]

    resp = client.post(
        f"/api/v1/audits/{session_id}/manual",
        json={"equipment_id": str(equipment_item.id), "is_present": False},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_present"] is False
    assert resp.json()["check_method"] == "manual"


def test_complete_session(client, auth_headers, location, equipment_item):
    r = client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    session_id = r.json()["id"]

    resp = client.post(f"/api/v1/audits/{session_id}/complete", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["completed_at"] is not None


def test_complete_already_completed(client, auth_headers, location, equipment_item):
    r = client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    session_id = r.json()["id"]
    client.post(f"/api/v1/audits/{session_id}/complete", headers=auth_headers)

    resp = client.post(f"/api/v1/audits/{session_id}/complete", headers=auth_headers)
    assert resp.status_code == 409


def test_report(client, auth_headers, location, equipment_item):
    r = client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    session_id = r.json()["id"]

    # Mark present via scan
    client.post(
        f"/api/v1/audits/{session_id}/scan",
        json={"qr_code": equipment_item.qr_code},
        headers=auth_headers,
    )
    client.post(f"/api/v1/audits/{session_id}/complete", headers=auth_headers)

    resp = client.get(f"/api/v1/audits/{session_id}/report", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["present"] == 1
    assert data["summary"]["missing"] == 0
    assert data["summary"]["unchecked"] == 0
    assert len(data["present_items"]) == 1
    assert data["present_items"][0]["name"] == "Laptop 1"


def test_new_audit_starts_after_complete(client, auth_headers, location, equipment_item):
    r = client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    session_id = r.json()["id"]
    client.post(f"/api/v1/audits/{session_id}/complete", headers=auth_headers)

    # Should be able to start a new audit now
    resp = client.post("/api/v1/audits", json={"location_id": str(location.id)}, headers=auth_headers)
    assert resp.status_code == 201
