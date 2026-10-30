"""Integration tests for API-03: Edge Ingestion & Fatigue Incident History."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.database import Base, get_db
from app.main import app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine, autoflush=False, autocommit=False
)


@pytest.fixture(autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    """Recreate test schema tables for clean state."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """TestClient with in-memory database dependency override."""

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def paired_device(client: TestClient) -> dict[str, str | int]:
    """Helper creating user, family, and paired edge device."""
    res_u = client.post(
        "/api/v1/auth/register",
        json={"name": "Sopir", "email": "s@ex.com", "password": "Pass123!"},
    )
    user_token = res_u.json()["access_token"]
    headers = {"Authorization": f"Bearer {user_token}"}
    res_f = client.post(
        "/api/v1/families", json={"name": "Keluarga"}, headers=headers
    )
    family_id = res_f.json()["id"]

    device_uid = "pi4_car"
    device_key = "key123"
    res_d = client.post(
        f"/api/v1/families/{family_id}/devices",
        json={"device_uid": device_uid, "vehicle_name": "Innova", "api_key": device_key},
        headers=headers,
    )
    assert res_d.status_code == 201

    return {
        "user_token": user_token,
        "family_id": family_id,
        "device_uid": device_uid,
        "device_key": device_key,
    }


def test_heartbeat_telemetry_flow(
    client: TestClient, paired_device: dict[str, str | int]
) -> None:
    """Verify heartbeat updates device position, speed, and online state."""
    uid, key, fam_id, tok = (
        paired_device["device_uid"],
        paired_device["device_key"],
        paired_device["family_id"],
        paired_device["user_token"],
    )
    hb_data = {
        "device_uid": uid,
        "state": "DRIVING",
        "drowsy_confidence": 0.1,
        "yawn_confidence": 0.05,
        "location": {"lat": -1.265, "lng": 116.831, "speed_kmh": 68.5},
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
    }
    res_hb = client.post(
        "/api/v1/edge/heartbeat", json=hb_data, headers={"X-Device-API-Key": str(key)}
    )
    assert res_hb.status_code == 200
    assert res_hb.json()["status"] == "ok"

    res_ov = client.get(
        f"/api/v1/families/{fam_id}/overview",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert res_ov.status_code == 200
    dev = res_ov.json()["devices"][0]
    assert dev["is_online"] is True
    assert dev["last_speed_kmh"] == 68.5


def test_heartbeat_auth_failures(
    client: TestClient, paired_device: dict[str, str | int]
) -> None:
    """Verify heartbeat rejects missing, invalid, or mismatched keys."""
    uid = paired_device["device_uid"]
    payload = {"device_uid": uid, "state": "DRIVING"}

    assert client.post("/api/v1/edge/heartbeat", json=payload).status_code == 401
    assert (
        client.post(
            "/api/v1/edge/heartbeat",
            json=payload,
            headers={"X-Device-API-Key": "bad_key"},
        ).status_code
        == 401
    )
    res_mis = client.post(
        "/api/v1/edge/heartbeat",
        json={"device_uid": "other_pi", "state": "DRIVING"},
        headers={"X-Device-API-Key": str(paired_device["device_key"])},
    )
    assert res_mis.status_code == 403


def test_incident_record_and_query(
    client: TestClient, paired_device: dict[str, str | int]
) -> None:
    """Verify recording fatigue incident and querying historical log."""
    uid, key, fam_id, tok = (
        paired_device["device_uid"],
        paired_device["device_key"],
        paired_device["family_id"],
        paired_device["user_token"],
    )
    headers = {"Authorization": f"Bearer {tok}"}
    edge_hdrs = {"X-Device-API-Key": str(key)}

    # Record CRITICAL_DROWSY
    res_1 = client.post(
        "/api/v1/edge/incidents",
        json={
            "device_uid": uid,
            "incident_type": "CRITICAL_DROWSY",
            "confidence_score": 0.9,
            "duration_seconds": 2.5,
            "location": {"lat": -1.27, "lng": 116.84, "speed_kmh": 70.0},
            "recorded_at": int(datetime.now(timezone.utc).timestamp()),
        },
        headers=edge_hdrs,
    )
    assert res_1.status_code == 201

    # Record WARNING_FATIGUE
    res_2 = client.post(
        "/api/v1/edge/incidents",
        json={
            "device_uid": uid,
            "incident_type": "WARNING_FATIGUE",
            "confidence_score": 0.8,
            "duration_seconds": 1.5,
            "recorded_at": int(datetime.now(timezone.utc).timestamp()) + 5,
        },
        headers=edge_hdrs,
    )
    assert res_2.status_code == 201

    # Query family incidents
    res_list = client.get(f"/api/v1/families/{fam_id}/incidents", headers=headers)
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) == 2
    assert items[0]["incident_type"] == "WARNING_FATIGUE"

    # Filter by incident_type
    res_f = client.get(
        f"/api/v1/families/{fam_id}/incidents?incident_type=CRITICAL_DROWSY",
        headers=headers,
    )
    assert res_f.status_code == 200
    assert len(res_f.json()) == 1

    # Forbidden for non-member
    res_out = client.post(
        "/api/v1/auth/register",
        json={"name": "Out", "email": "out@ex.com", "password": "Password123!"},
    )
    bad_h = {"Authorization": f"Bearer {res_out.json()['access_token']}"}
    assert (
        client.get(f"/api/v1/families/{fam_id}/incidents", headers=bad_h).status_code
        == 403
    )
