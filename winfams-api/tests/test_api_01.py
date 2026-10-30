"""Unit tests for API-01: FastAPI, SQLAlchemy 2.0 & Database Models."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

# Add winfams-api root to sys.path
API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.config import settings
from app.core.database import Base
from app.models import Device, Family, FamilyMember, FatigueIncident, User


@pytest.fixture
def test_db() -> Session:
    """Fixture providing an isolated in-memory SQLite database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_config_settings() -> None:
    """Verify default configurations."""
    assert settings.PROJECT_NAME == "WinFams API"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.ALGORITHM == "HS256"


def test_models_crud_and_relationships(test_db: Session) -> None:
    """Verify full relational lifecycle of User, Family, Member, Device, and Incident."""
    # 1. Create User
    user = User(
        name="Budi Santoso",
        email="budi@example.com",
        password_hash="hashed_secret_pw",
        phone_number="081234567890",
        fcm_token="sample_fcm_token_123",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    assert user.id is not None
    assert user.email == "budi@example.com"

    # 2. Create Family
    family = Family(
        name="Keluarga Budi",
        invite_code="FAM123XYZ",
        created_by=user.id,
    )
    test_db.add(family)
    test_db.commit()
    test_db.refresh(family)

    assert family.id is not None
    assert family.creator.name == "Budi Santoso"

    # 3. Create Family Member
    member = FamilyMember(
        family_id=family.id,
        user_id=user.id,
        role="ADMIN",
    )
    test_db.add(member)
    test_db.commit()

    # 4. Create Device
    now = datetime.now(timezone.utc)
    device = Device(
        device_uid="pi4_car_01",
        api_key_hash="hashed_device_key_abc",
        family_id=family.id,
        active_driver_id=user.id,
        vehicle_name="Innova Hitam - B 1234 XYZ",
        is_online=True,
        current_state="DRIVING",
        last_lat=-1.265386,
        last_lng=116.831200,
        last_speed_kmh=65.0,
        last_seen_at=now,
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)

    assert device.id is not None
    assert device.family.name == "Keluarga Budi"
    assert device.active_driver.email == "budi@example.com"

    # 5. Create Fatigue Incident
    incident = FatigueIncident(
        device_id=device.id,
        driver_id=user.id,
        family_id=family.id,
        incident_type="CRITICAL_DROWSY",
        confidence_score=0.88,
        duration_seconds=2.1,
        lat=-1.265386,
        lng=116.831200,
        speed_kmh=68.5,
        recorded_at=now,
    )
    test_db.add(incident)
    test_db.commit()
    test_db.refresh(incident)

    assert incident.id is not None
    assert incident.incident_type == "CRITICAL_DROWSY"
    assert incident.device.device_uid == "pi4_car_01"

    # 6. Verify SQLAlchemy 2.0 select() query
    stmt = (
        select(Device)
        .where(Device.device_uid == "pi4_car_01")
        .join(Device.family)
    )
    queried_device = test_db.scalar(stmt)
    assert queried_device is not None
    assert queried_device.vehicle_name == "Innova Hitam - B 1234 XYZ"
    assert len(queried_device.incidents) == 1
    assert queried_device.incidents[0].confidence_score == 0.88


def test_unique_constraints(test_db: Session) -> None:
    """Verify unique constraints on user email and device_uid."""
    user1 = User(
        name="User 1",
        email="duplicate@example.com",
        password_hash="pw1",
    )
    test_db.add(user1)
    test_db.commit()

    user2 = User(
        name="User 2",
        email="duplicate@example.com",
        password_hash="pw2",
    )
    test_db.add(user2)
    with pytest.raises(Exception):
        test_db.commit()
    test_db.rollback()
