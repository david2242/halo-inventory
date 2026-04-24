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
        id=uuid.uuid4(),
        email="director@test.hu",
        full_name="Director",
        role=UserRole.director,
        password_hash=hash_password("pass1234"),
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def delegate(test_db: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="delegate@test.hu",
        full_name="Delegate",
        role=UserRole.delegate,
        password_hash=hash_password("pass1234"),
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def director_headers(client, director):
    r = client.post("/api/v1/auth/login", json={"email": "director@test.hu", "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def delegate_headers(client, delegate):
    r = client.post("/api/v1/auth/login", json={"email": "delegate@test.hu", "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_list_users_director(client, director_headers, director):
    resp = client.get("/api/v1/users", headers=director_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["email"] == "director@test.hu"


def test_list_users_delegate_forbidden(client, delegate_headers):
    resp = client.get("/api/v1/users", headers=delegate_headers)
    assert resp.status_code == 403


def test_create_user(client, director_headers):
    resp = client.post(
        "/api/v1/users",
        json={"email": "new@test.hu", "full_name": "New User", "role": "delegate", "password": "newpass1"},
        headers=director_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@test.hu"
    assert resp.json()["role"] == "delegate"
    assert resp.json()["is_active"] is True


def test_create_user_duplicate_email(client, director_headers, director):
    resp = client.post(
        "/api/v1/users",
        json={"email": "director@test.hu", "full_name": "Dup", "role": "delegate", "password": "pass1234"},
        headers=director_headers,
    )
    assert resp.status_code == 409


def test_create_user_short_password(client, director_headers):
    resp = client.post(
        "/api/v1/users",
        json={"email": "short@test.hu", "full_name": "Short", "role": "delegate", "password": "abc"},
        headers=director_headers,
    )
    assert resp.status_code == 422


def test_get_user(client, director_headers, director):
    resp = client.get(f"/api/v1/users/{director.id}", headers=director_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == str(director.id)


def test_get_user_not_found(client, director_headers):
    resp = client.get(f"/api/v1/users/{uuid.uuid4()}", headers=director_headers)
    assert resp.status_code == 404


def test_update_user_role(client, director_headers, delegate):
    resp = client.put(
        f"/api/v1/users/{delegate.id}",
        json={"role": "director"},
        headers=director_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "director"


def test_deactivate_user(client, director_headers, delegate):
    resp = client.delete(f"/api/v1/users/{delegate.id}", headers=director_headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_cannot_deactivate_self(client, director_headers, director):
    resp = client.delete(f"/api/v1/users/{director.id}", headers=director_headers)
    assert resp.status_code == 400


def test_delegate_cannot_create_user(client, delegate_headers):
    resp = client.post(
        "/api/v1/users",
        json={"email": "x@test.hu", "full_name": "X", "role": "delegate", "password": "pass1234"},
        headers=delegate_headers,
    )
    assert resp.status_code == 403
