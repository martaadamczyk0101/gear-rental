import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import Hardware, HardwareStatus, User


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    session = testing_session_local()
    yield session
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture()
def client(db_session):
    # No `with` block: this intentionally avoids triggering the app's startup
    # event (which seeds/bootstraps against the real dev database), since
    # tests run against the isolated in-memory `db_session` engine instead.
    return TestClient(app)


@pytest.fixture()
def admin_user(db_session):
    user = User(email="admin@test.com", password_hash=hash_password("pw"), is_admin=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def regular_user(db_session):
    user = User(email="user@test.com", password_hash=hash_password("pw"), is_admin=False)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def other_user(db_session):
    user = User(email="other@test.com", password_hash=hash_password("pw"), is_admin=False)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def available_hardware(db_session):
    hardware = Hardware(name="Test Laptop", brand="TestBrand", status=HardwareStatus.AVAILABLE)
    db_session.add(hardware)
    db_session.commit()
    db_session.refresh(hardware)
    return hardware


@pytest.fixture()
def in_repair_hardware(db_session):
    hardware = Hardware(name="Broken Mouse", brand="TestBrand", status=HardwareStatus.IN_REPAIR)
    db_session.add(hardware)
    db_session.commit()
    db_session.refresh(hardware)
    return hardware
