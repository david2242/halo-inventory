import uuid
from typing import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base
from app.models.equipment import EquipmentCategory, EquipmentStatus
from app.models.location import Location
from app.models.user import User, UserRole


# SQLite in-memory engine for unit tests (no PostgreSQL needed)
@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # SQLite doesn't enforce FK by default
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def location(db: Session) -> Location:
    loc = Location(id=uuid.uuid4(), name="Teszt Telephely", address="1234 Budapest")
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@pytest.fixture
def director_user(db: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="director@test.hu",
        full_name="Teszt Vezető",
        role=UserRole.director,
        password_hash="hashed",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
