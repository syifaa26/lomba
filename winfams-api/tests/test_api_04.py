"""Integration & unit tests for API-04: WebSocket Broadcaster & FCM Notifier."""

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
from starlette.websockets import WebSocketDisconnect

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.database import Base, get_db
from app.main import app
from app.services.fcm_notifier import fcm_notifier

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
    """Recreate test schema tables for each test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """TestClient configured with in-memory database override."""

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
def family_setup(client: TestClient) -> dict[str, str | int]:
    """Create driver, monitor with FCM token, family group, and paired device."""
    res_d = client.post(
        "/api/v1/auth/register",
        json={"name": "Ayah", "email": "ayah@ex.com", "password": "Password123!"},
    )
    driver_token = res_d.json()["access_token"]
    driver_hdrs = {"Authorization": f"Bearer {driver_token}"}

    res_m = client.post(
        "/api/v1/auth/register",
        json={"name": "Ibu", "email": "ibu@ex.com", "password": "Password123!"},
    )
    monitor_token = res_m.json()["access_token"]
    monitor_id = res_m.json()["user"]["id"]
    monitor_hdrs = {"Authorization": f"Bearer {monitor_token}"}
    client.put(
        "/api/v1/auth/fcm-token",
        json={"fcm_token": "fcm_token_ibu_phone_xyz"},
        headers=monitor_hdrs,
    )

    res_f = client.post(
        "/api/v1/families", json={"name": "Keluarga"}, headers=driver_hdrs
    )
    family_id = res_f.json()["id"]
    invite_code = res_f.json()["invite_code"]

    client.post(
        "/api/v1/families/join",
        json={"invite_code": invite_code, "role": "MONITOR"},
        headers=monitor_hdrs,
    )

    device_uid = "pi4_rush_01"
    device_key = "secret_pi_key_777"
    client.post(
        f"/api/v1/families/{family_id}/devices",
        json={"device_uid": device_uid, "vehicle_name": "Rush", "api_key": device_key},
        headers=driver_hdrs,
    )

    return {
        "family_id": family_id,
        "driver_token": driver_token,
        "monitor_token": monitor_token,
        "monitor_id": monitor_id,
        "device_uid": device_uid,
        "device_key": device_key,
    }


def test_ws_handshake_and_ping(
    client: TestClient, family_setup: dict[str, str | int]
) -> None:
    """Verify WebSocket handshake and bidirectional ping/pong."""
    fam_id = family_setup["family_id"]
    tok = family_setup["monitor_token"]
    mid = family_setup["monitor_id"]

    with client.websocket_connect(f"/ws/families/{fam_id}?token={tok}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "CONNECTION_ESTABLISHED"
        assert msg["family_id"] == fam_id
        assert msg["user_id"] == mid

        ws.send_text("ping")
        assert ws.receive_text() == "pong"


def test_ws_auth_rejection(
    client: TestClient, family_setup: dict[str, str | int]
) -> None:
    """Verify WebSocket connection rejects invalid, missing, or outsider tokens."""
    fam_id = family_setup["family_id"]

    # 1. Missing token
    with pytest.raises(WebSocketDisconnect) as exc1:
        with client.websocket_connect(f"/ws/families/{fam_id}"):
            pass
    assert exc1.value.code == 1008

    # 2. Invalid JWT token
    with pytest.raises(WebSocketDisconnect) as exc2:
        with client.websocket_connect(f"/ws/families/{fam_id}?token=bad_jwt"):
            pass
    assert exc2.value.code == 1008

    # 3. Outsider token
    res_out = client.post(
        "/api/v1/auth/register",
        json={"name": "Out", "email": "out@ex.com", "password": "Password123!"},
    )
    out_tok = res_out.json()["access_token"]
    with pytest.raises(WebSocketDisconnect) as exc3:
        with client.websocket_connect(f"/ws/families/{fam_id}?token={out_tok}"):
            pass
    assert exc3.value.code == 1008


def test_heartbeat_and_incident_broadcast(
    client: TestClient, family_setup: dict[str, str | int]
) -> None:
    """Verify live telemetry and emergency fatigue alerts are received via WebSocket."""
    fam_id, tok = family_setup["family_id"], family_setup["monitor_token"]
    uid, key = str(family_setup["device_uid"]), str(family_setup["device_key"])

    with client.websocket_connect(f"/ws/families/{fam_id}?token={tok}") as ws:
        assert ws.receive_json()["type"] == "CONNECTION_ESTABLISHED"

        # 1. Post telemetry heartbeat
        hb = {
            "device_uid": uid,
            "state": "DRIVING",
            "location": {"lat": -1.265, "lng": 116.831, "speed_kmh": 65.0},
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
        }
        res_hb = client.post(
            "/api/v1/edge/heartbeat", json=hb, headers={"X-Device-API-Key": key}
        )
        assert res_hb.status_code == 200

        ws_msg = ws.receive_json()
        assert ws_msg["type"] == "DEVICE_TELEMETRY"
        assert ws_msg["device_uid"] == uid
        assert ws_msg["location"]["speed_kmh"] == 65.0

        # 2. Post CRITICAL_DROWSY incident
        inc = {
            "device_uid": uid,
            "incident_type": "CRITICAL_DROWSY",
            "confidence_score": 0.95,
            "duration_seconds": 2.8,
            "location": {"lat": -1.27, "lng": 116.84, "speed_kmh": 72.0},
            "recorded_at": int(datetime.now(timezone.utc).timestamp()),
        }
        res_inc = client.post(
            "/api/v1/edge/incidents", json=inc, headers={"X-Device-API-Key": key}
        )
        assert res_inc.status_code == 201

        alert_msg = ws.receive_json()
        assert alert_msg["type"] == "FATIGUE_ALERT"
        assert alert_msg["incident_type"] == "CRITICAL_DROWSY"
        assert alert_msg["location"]["speed_kmh"] == 72.0


def test_fcm_notifier_unit(family_setup: dict[str, str | int]) -> None:
    """Verify FCM service dispatches notification to registered tokens."""
    db = TestingSessionLocal()
    try:
        sent = fcm_notifier.send_emergency_fatigue_alert(
            db=db,
            family_id=int(family_setup["family_id"]),
            driver_name="Ayah",
            vehicle_name="Rush",
            incident_type="CRITICAL_DROWSY",
            speed_kmh=80.0,
            lat=-1.265,
            lng=116.831,
        )
        assert sent == 1
    finally:
        db.close()
