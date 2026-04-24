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

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
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
        id=uuid.uuid4(),
        email="director@test.hu",
        full_name="Vezető",
        role=UserRole.director,
        password_hash=hash_password("password123"),
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def auth_headers(client: TestClient, director: User) -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": "director@test.hu", "password": "password123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def location(test_db: Session) -> Location:
    loc = Location(id=uuid.uuid4(), name="Teszt Telephely", address="1234 Budapest")
    test_db.add(loc)
    test_db.commit()
    return loc


def test_list_locations_ordered(client, auth_headers, test_db):
    loc_a = Location(id=uuid.uuid4(), name="Aaa Telephely")
    loc_b = Location(id=uuid.uuid4(), name="Zzz Telephely")
    test_db.add_all([loc_b, loc_a])
    test_db.commit()

    resp = client.get("/api/v1/locations", headers=auth_headers)
    assert resp.status_code == 200
    names = [i["name"] for i in resp.json()["items"]]
    assert names == sorted(names)


def test_create_location(client, auth_headers):
    resp = client.post("/api/v1/locations", json={"name": "Új Telephely", "address": "Pécs"}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Új Telephely"


def test_create_location_duplicate_name(client, auth_headers, location):
    resp = client.post("/api/v1/locations", json={"name": "Teszt Telephely"}, headers=auth_headers)
    assert resp.status_code == 409


def test_get_location_detail(client, auth_headers, location):
    resp = client.get(f"/api/v1/locations/{location.id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(location.id)
    assert "equipment_count" in data
    assert data["equipment_count"] == 0


def test_get_location_not_found(client, auth_headers):
    resp = client.get(f"/api/v1/locations/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


def test_update_location(client, auth_headers, location):
    resp = client.put(f"/api/v1/locations/{location.id}",
                      json={"name": "Átnevezett Telephely"},
                      headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Átnevezett Telephely"


def test_delete_location_empty(client, auth_headers, location):
    resp = client.delete(f"/api/v1/locations/{location.id}", headers=auth_headers)
    assert resp.status_code == 204


def test_delete_location_with_equipment(client, auth_headers, location, test_db, director):
    eq = Equipment(
        id=uuid.uuid4(),
        name="Laptop",
        category=EquipmentCategory.laptop,
        qr_code=f"halo-inv://{uuid.uuid4()}",
        location_id=location.id,
        created_by_id=director.id,
        status=EquipmentStatus.active,
    )
    test_db.add(eq)
    test_db.commit()

    resp = client.delete(f"/api/v1/locations/{location.id}", headers=auth_headers)
    assert resp.status_code == 409


def test_location_requires_auth(client):
    resp = client.get("/api/v1/locations")
    assert resp.status_code in (401, 403)
