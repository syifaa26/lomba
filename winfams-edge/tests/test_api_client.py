"""Unit and integration tests for SYNC-02: ApiClient & BackgroundSyncWorker."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EDGE_ROOT = Path(__file__).resolve().parent.parent
if str(EDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(EDGE_ROOT))

from schemas.payload import FatigueIncident, HeartbeatPayload, IncidentPayload, LocationData
from services.api_client import ApiClient, BackgroundSyncWorker
from services.local_cache import LocalCache


@pytest.fixture
def temp_cache(tmp_path: Path) -> LocalCache:
    """Fixture providing isolated temporary SQLite cache."""
    db_file = tmp_path / "test_offline.db"
    cache = LocalCache(db_path=db_file)
    yield cache
    cache.close()


def test_api_client_heartbeat_success() -> None:
    """Verify ApiClient formats and sends heartbeat correctly."""
    client = ApiClient(base_url="http://testserver", api_key="test_key_123")
    hb = HeartbeatPayload(
        device_uid="pi4_test",
        state="DRIVING",
        drowsy_confidence=0.1,
        yawn_confidence=0.0,
        location=LocationData(lat=-1.265, lng=116.831, speed_kmh=60.0),
        timestamp=1730000000,
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch.object(client.session, "post", return_value=mock_resp) as mock_post:
        success = client.send_heartbeat(hb)
        assert success is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://testserver/api/v1/edge/heartbeat"
        assert kwargs["json"]["device_uid"] == "pi4_test"


def test_api_client_incident_network_error() -> None:
    """Verify ApiClient returns False gracefully on network exception."""
    client = ApiClient(base_url="http://badserver", api_key="key")
    inc = IncidentPayload(
        device_uid="pi4_test",
        incident_type="CRITICAL_DROWSY",
        confidence_score=0.9,
        duration_seconds=2.0,
        location=LocationData(),
        recorded_at=1730000000,
    )
    with patch.object(client.session, "post", side_effect=Exception("Connection refused")):
        assert client.send_incident(inc) is False


def test_sync_worker_offline_fallback_and_flush(temp_cache: LocalCache) -> None:
    """Verify worker enqueues to SQLite when offline and flushes when online."""
    mock_api = MagicMock(spec=ApiClient)
    # Simulate API initially offline
    mock_api.send_incident.return_value = False

    worker = BackgroundSyncWorker(
        api_client=mock_api,
        local_cache=temp_cache,
        heartbeat_interval_sec=0.5,
    )

    incident = FatigueIncident(
        incident_id="inc_offline_001",
        device_id="pi4_car",
        driver_uid="usr_1",
        family_group_id="fam_1",
        type="CRITICAL_DROWSY",
        confidence_score=0.95,
        duration_seconds=2.5,
        location=LocationData(lat=-1.2, lng=116.8, speed_kmh=65.0),
        timestamp=1730000000,
    )

    worker.start()
    try:
        # 1. Enqueue while offline
        worker.enqueue_incident(incident)
        time.sleep(0.6)  # allow worker loop to process queue

        # LocalCache should now hold 1 queued incident
        assert temp_cache.count() == 1

        # 2. Simulate API back online
        mock_api.send_incident.return_value = True
        mock_api.send_heartbeat.return_value = True

        # Provide a heartbeat to trigger flush during loop
        hb = HeartbeatPayload(
            device_uid="pi4_car",
            state="DRIVING",
            drowsy_confidence=0.0,
            yawn_confidence=0.0,
            location=LocationData(),
            timestamp=1730000010,
        )
        worker.update_telemetry(hb)
        time.sleep(0.8)

        # 3. LocalCache should now be fully flushed
        assert temp_cache.count() == 0

    finally:
        worker.stop()


def test_sync_worker_immediate_online_send(temp_cache: LocalCache) -> None:
    """Verify worker sends incident immediately without touching SQLite when online."""
    mock_api = MagicMock(spec=ApiClient)
    mock_api.send_incident.return_value = True

    worker = BackgroundSyncWorker(
        api_client=mock_api,
        local_cache=temp_cache,
        heartbeat_interval_sec=1.0,
    )

    inc_payload = IncidentPayload(
        device_uid="pi4_car",
        incident_type="WARNING_FATIGUE",
        confidence_score=0.8,
        duration_seconds=1.2,
        location=LocationData(),
        recorded_at=1730000020,
    )

    worker.start()
    try:
        worker.enqueue_incident(inc_payload)
        time.sleep(0.4)
        mock_api.send_incident.assert_called_with(inc_payload)
        assert temp_cache.count() == 0
    finally:
        worker.stop()

