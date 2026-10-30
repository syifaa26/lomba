"""Unit tests for SYNC-02: Firebase Cloud Sync Service (services/cloud_sync.py)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.detector import MockDetector
from core.state_machine import DriverState, FatigueStateMachine
from hardware.buzzer_controller import BuzzerController
from hardware.gps_reader import GPSReader
from main import EdgeOrchestrator
from schemas.payload import DeviceStatus, FatigueIncident, LocationData
from services.cloud_sync import CloudSyncService
from services.local_cache import LocalCache


def create_dummy_incident(
    incident_id: str = "inc_sync_001",
    incident_type: str = "CRITICAL_DROWSY",
) -> FatigueIncident:
    """Helper creating a sample FatigueIncident."""
    return FatigueIncident(
        incident_id=incident_id,
        device_id="pi4_car_01",
        driver_uid="user_123",
        family_group_id="fam_001",
        type=incident_type,
        confidence_score=0.91,
        duration_seconds=1.8,
        location=LocationData(lat=-1.265386, lng=116.831200, speed_kmh=70.0, heading=90.0),
        timestamp=int(time.time()),
        resolved=False,
    )


def test_cloud_sync_initialization(tmp_path: Path) -> None:
    """Test CloudSyncService initializes cleanly in mock mode."""
    cache = LocalCache(db_path=tmp_path / "sync.db")
    service = CloudSyncService(local_cache=cache, force_mock=True)
    assert service.is_mock is True
    assert len(service.mock_statuses) == 0
    assert len(service.mock_incidents) == 0
    service.stop()
    cache.close()


def test_cloud_sync_upload_status(tmp_path: Path) -> None:
    """Test uploading DeviceStatus to realtime database."""
    cache = LocalCache(db_path=tmp_path / "sync.db")
    service = CloudSyncService(local_cache=cache, force_mock=True)

    status = DeviceStatus(
        device_id="pi4_car_01",
        driver_uid="user_123",
        is_online=True,
        state="DRIVING",
        drowsy_confidence=0.1,
        yawn_confidence=0.05,
        location=LocationData(lat=-1.26, lng=116.83, speed_kmh=60.0, heading=180.0),
        last_updated=int(time.time()),
    )

    success = service.upload_status(status)
    assert success is True
    assert len(service.mock_statuses) == 1
    assert service.mock_statuses[0]["device_id"] == "pi4_car_01"
    assert service.mock_statuses[0]["location"]["speed_kmh"] == 60.0

    service.stop()
    cache.close()


def test_cloud_sync_upload_incident_and_fcm(tmp_path: Path) -> None:
    """Test uploading FatigueIncident stores document and emits FCM message."""
    cache = LocalCache(db_path=tmp_path / "sync.db")
    service = CloudSyncService(local_cache=cache, force_mock=True)

    incident = create_dummy_incident("inc_test_100")
    success = service.upload_incident(incident)

    assert success is True
    assert len(service.mock_incidents) == 1
    assert service.mock_incidents[0]["incident_id"] == "inc_test_100"
    assert len(service.mock_fcm_messages) == 1
    assert service.mock_fcm_messages[0]["topic"] == "family_fam_001"
    assert service.mock_fcm_messages[0]["type"] == "CRITICAL_DROWSY"

    service.stop()
    cache.close()


def test_cloud_sync_offline_buffering_and_reconnect_flush(tmp_path: Path) -> None:
    """Test offline buffering to LocalCache and automatic flushing upon reconnection."""
    cache = LocalCache(db_path=tmp_path / "sync.db")
    service = CloudSyncService(
        local_cache=cache,
        force_mock=True,
        telemetry_interval_sec=0.2,
    )

    # 1. Simulate offline state: upload should fail and incident buffered
    service.simulate_offline = True
    incident = create_dummy_incident("inc_offline_01")

    service.start()
    service.report_incident(incident)

    # Give worker a moment to process the queue
    time.sleep(0.3)
    assert cache.count() == 1
    assert len(service.mock_incidents) == 0

    # 2. Simulate reconnection: worker should flush offline queue
    service.simulate_offline = False
    flushed = service.flush_offline_queue()

    assert flushed == 1
    assert cache.count() == 0
    assert len(service.mock_incidents) == 1
    assert service.mock_incidents[0]["incident_id"] == "inc_offline_01"

    service.stop()
    cache.close()


def test_orchestrator_integration_with_cloud_sync(tmp_path: Path) -> None:
    """Test EdgeOrchestrator seamlessly delivers telemetry and incidents to CloudSyncService."""
    cache = LocalCache(db_path=tmp_path / "sync.db")
    cloud_sync = CloudSyncService(local_cache=cache, force_mock=True)

    detector = MockDetector(face_detected=True, drowsy_confidence=0.9, yawn_confidence=0.0)
    buzzer = BuzzerController(force_mock=True)
    gps = GPSReader(force_mock=True, mock_lat=-1.2653, mock_lng=116.8312)
    state_machine = FatigueStateMachine(drowsy_time_sec=1.0)

    class MockCamera:
        def start(self) -> MockCamera:
            return self

        def read(self) -> tuple[bool, np.ndarray]:
            return True, np.zeros((480, 640, 3), dtype=np.uint8)

        def stop(self) -> None:
            pass

    orchestrator = EdgeOrchestrator(
        camera=MockCamera(),
        detector=detector,
        buzzer=buzzer,
        gps=gps,
        cloud_sync=cloud_sync,
        state_machine=state_machine,
    )

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Step 1: Normal step (t=1000s)
    orchestrator.step(frame=dummy_frame, current_time=1000.0)
    assert cloud_sync._latest_status is not None
    assert cloud_sync._latest_status.drowsy_confidence == 0.9

    # Step 2: Critical step (t=1001.5s >= 1.0s)
    orchestrator.step(frame=dummy_frame, current_time=1001.5)
    assert not cloud_sync._incident_queue.empty()
    queued_inc = cloud_sync._incident_queue.get_nowait()
    assert queued_inc.type == DriverState.CRITICAL_DROWSY.value

    orchestrator.stop()
    cache.close()

