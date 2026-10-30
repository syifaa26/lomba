"""Isolated unit tests for Task EDGE-01 (config and schemas)."""

import json
import sys
from pathlib import Path

# Add project root to sys.path
EDGE_ROOT = Path(__file__).resolve().parent.parent
if str(EDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(EDGE_ROOT))

from config import settings
from schemas.payload import (
    DeviceStatus,
    FatigueIncident,
    HeartbeatPayload,
    IncidentPayload,
    LocationData,
)


def test_settings_defaults() -> None:
    """Verify that configuration settings match the PRD thresholds."""
    assert settings.BLINK_THRESHOLD == 0.55
    assert settings.YAWN_THRESHOLD == 0.60
    assert settings.DROWSY_TIME_SEC == 1.5
    assert settings.YAWN_TIME_SEC == 2.5
    assert settings.YAWN_COUNT_TRIGGER == 3
    assert settings.YAWN_WINDOW_SEC == 600.0
    assert settings.BUZZER_PIN == 17
    assert settings.TELEMETRY_INTERVAL_SEC == 10.0
    assert settings.SPEED_THRESHOLD_KMH == 5.0
    assert settings.DEVICE_UID == "pi4_car_01"
    assert settings.API_BASE_URL == "http://localhost:8000"
    logger = settings.setup_logging()
    assert logger.name == "winfams"


def test_heartbeat_payload_serialization() -> None:
    """Verify HeartbeatPayload matches PRD JSON contract."""
    loc = LocationData(lat=-1.265386, lng=116.831200, speed_kmh=64.5)
    heartbeat = HeartbeatPayload(
        device_uid="pi4_car_01",
        state="DRIVING",
        drowsy_confidence=0.12,
        yawn_confidence=0.05,
        location=loc,
        timestamp=1730334600,
    )
    data = heartbeat.to_dict()
    assert data["device_uid"] == "pi4_car_01"
    assert data["location"]["lat"] == -1.265386
    assert data["state"] == "DRIVING"

    reconstructed = HeartbeatPayload.from_json(heartbeat.to_json())
    assert reconstructed.device_uid == heartbeat.device_uid
    assert reconstructed.drowsy_confidence == 0.12


def test_incident_payload_serialization() -> None:
    """Verify IncidentPayload matches PRD JSON contract."""
    loc = LocationData(lat=-1.265386, lng=116.831200, speed_kmh=72.0)
    incident = IncidentPayload(
        device_uid="pi4_car_01",
        incident_type="CRITICAL_DROWSY",
        confidence_score=0.88,
        duration_seconds=2.1,
        location=loc,
        recorded_at=1730334605,
    )
    data = incident.to_dict()
    assert data["device_uid"] == "pi4_car_01"
    assert data["incident_type"] == "CRITICAL_DROWSY"
    assert data["duration_seconds"] == 2.1

    reconstructed = IncidentPayload.from_json(incident.to_json())
    assert reconstructed.device_uid == incident.device_uid
    assert reconstructed.confidence_score == 0.88


def test_device_status_serialization() -> None:
    """Verify DeviceStatus serialization matches the PRD JSON contract."""
    location = LocationData(
        lat=-1.265386,
        lng=116.831200,
        speed_kmh=64.5,
        heading=180.0,
    )
    status = DeviceStatus(
        device_id="pi4_car_01",
        driver_uid="user_123",
        is_online=True,
        state="DRIVING",
        drowsy_confidence=0.12,
        yawn_confidence=0.05,
        location=location,
        last_updated=1730334600,
    )

    data = status.to_dict()
    assert data["device_id"] == "pi4_car_01"
    assert data["location"]["lat"] == -1.265386
    assert data["location"]["speed_kmh"] == 64.5

    json_str = status.to_json()
    reconstructed = DeviceStatus.from_json(json_str)
    assert reconstructed.device_id == status.device_id
    assert reconstructed.location.lat == status.location.lat
    assert reconstructed.is_online is True


def test_fatigue_incident_serialization() -> None:
    """Verify FatigueIncident serialization matches the PRD JSON contract."""
    location = LocationData(
        lat=-1.265386,
        lng=116.831200,
        speed_kmh=72.0,
        heading=0.0,
    )
    incident = FatigueIncident(
        incident_id="inc_987654",
        device_id="pi4_car_01",
        driver_uid="user_123",
        family_group_id="fam_001",
        type="CRITICAL_DROWSY",
        confidence_score=0.88,
        duration_seconds=2.1,
        location=location,
        timestamp=1730334605,
        resolved=False,
    )

    incident_dict = incident.to_dict()
    assert incident_dict["incident_id"] == "inc_987654"
    assert incident_dict["duration_seconds"] == 2.1
    assert incident_dict["type"] == "CRITICAL_DROWSY"

    json_str = incident.to_json()
    reconstructed = FatigueIncident.from_json(json_str)
    assert reconstructed.incident_id == incident.incident_id
    assert reconstructed.type == "CRITICAL_DROWSY"
    assert reconstructed.duration_seconds == 2.1


def test_gps_none_tolerance() -> None:
    """Verify fault tolerance when GPS has not locked satellite (lat/lng = None)."""
    location = LocationData(lat=None, lng=None, speed_kmh=0.0, heading=0.0)
    status = DeviceStatus(
        device_id="pi4_car_01",
        driver_uid="user_123",
        is_online=True,
        state="NORMAL",
        drowsy_confidence=0.0,
        yawn_confidence=0.0,
        location=location,
        last_updated=1730334600,
    )
    assert status.location.lat is None
    assert status.location.lng is None
    assert status.to_dict()["location"]["lat"] is None
