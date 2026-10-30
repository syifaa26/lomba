"""Unit tests for SYNC-01: Local SQLite Offline Queue (services/local_cache.py)."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schemas.payload import FatigueIncident, LocationData
from services.local_cache import LocalCache


def create_dummy_incident(
    incident_id: str = "inc_test_1",
    timestamp: int = 1730334600,
    incident_type: str = "CRITICAL_DROWSY",
    lat: float | None = -1.265386,
    lng: float | None = 116.831200,
) -> FatigueIncident:
    """Helper creating a sample FatigueIncident."""
    return FatigueIncident(
        incident_id=incident_id,
        device_id="pi4_car_01",
        driver_uid="user_123",
        family_group_id="fam_001",
        type=incident_type,
        confidence_score=0.88,
        duration_seconds=2.1,
        location=LocationData(lat=lat, lng=lng, speed_kmh=64.5, heading=180.0),
        timestamp=timestamp,
        resolved=False,
    )


def test_local_cache_initialization(tmp_path: Path) -> None:
    """Test LocalCache creates database and initial count is zero."""
    db_file = tmp_path / "test_queue.db"
    cache = LocalCache(db_path=db_file)
    assert cache.count() == 0
    assert cache.peek() == []
    cache.close()


def test_local_cache_enqueue_and_peek(tmp_path: Path) -> None:
    """Test enqueueing incidents and retrieving them in FIFO order."""
    db_file = tmp_path / "test_queue.db"
    cache = LocalCache(db_path=db_file)

    inc1 = create_dummy_incident("inc_001", timestamp=100)
    inc2 = create_dummy_incident("inc_002", timestamp=200)
    inc3 = create_dummy_incident("inc_003", timestamp=150)

    assert cache.enqueue(inc1) is True
    assert cache.enqueue(inc2) is True
    assert cache.enqueue(inc3) is True
    assert cache.count() == 3

    # Duplicate enqueue with same ID should be ignored gracefully
    assert cache.enqueue(inc1) is False
    assert cache.count() == 3

    # Peek should return items ordered by timestamp ASC (100, 150, 200)
    items = cache.peek(limit=10)
    assert len(items) == 3
    assert items[0].incident_id == "inc_001"
    assert items[1].incident_id == "inc_003"
    assert items[2].incident_id == "inc_002"

    # Verify deep data integrity
    assert items[0].confidence_score == 0.88
    assert items[0].location.lat == -1.265386
    assert items[0].location.lng == 116.831200
    assert items[0].location.speed_kmh == 64.5

    cache.close()


def test_local_cache_peek_limit(tmp_path: Path) -> None:
    """Test peek respects maximum fetch limit."""
    db_file = tmp_path / "test_queue.db"
    with LocalCache(db_path=db_file) as cache:
        for i in range(5):
            cache.enqueue(create_dummy_incident(f"inc_{i}", timestamp=100 + i))

        assert cache.count() == 5
        peeked = cache.peek(limit=2)
        assert len(peeked) == 2
        assert peeked[0].incident_id == "inc_0"
        assert peeked[1].incident_id == "inc_1"


def test_local_cache_dequeue(tmp_path: Path) -> None:
    """Test dequeue removes specific synced incidents by ID."""
    db_file = tmp_path / "test_queue.db"
    with LocalCache(db_path=db_file) as cache:
        cache.enqueue(create_dummy_incident("inc_1", timestamp=100))
        cache.enqueue(create_dummy_incident("inc_2", timestamp=110))
        cache.enqueue(create_dummy_incident("inc_3", timestamp=120))

        # Dequeue inc_1 and inc_3
        deleted = cache.dequeue(["inc_1", "inc_3"])
        assert deleted == 2
        assert cache.count() == 1

        remaining = cache.peek()
        assert len(remaining) == 1
        assert remaining[0].incident_id == "inc_2"

        # Dequeue empty list does nothing
        assert cache.dequeue([]) == 0


def test_local_cache_clear(tmp_path: Path) -> None:
    """Test clearing all records."""
    db_file = tmp_path / "test_queue.db"
    with LocalCache(db_path=db_file) as cache:
        cache.enqueue(create_dummy_incident("inc_1"))
        cache.enqueue(create_dummy_incident("inc_2"))
        assert cache.count() == 2

        cache.clear()
        assert cache.count() == 0
        assert cache.peek() == []


def test_local_cache_null_location_handling(tmp_path: Path) -> None:
    """Test serialization and deserialization when GPS coordinates are None."""
    db_file = tmp_path / "test_queue.db"
    with LocalCache(db_path=db_file) as cache:
        inc = create_dummy_incident("inc_no_gps", lat=None, lng=None)
        cache.enqueue(inc)

        items = cache.peek()
        assert len(items) == 1
        assert items[0].location.lat is None
        assert items[0].location.lng is None


def test_local_cache_multithreaded_concurrency(tmp_path: Path) -> None:
    """Test thread-safety when multiple worker threads enqueue concurrently."""
    db_file = tmp_path / "test_queue.db"
    cache = LocalCache(db_path=db_file)

    num_threads = 5
    items_per_thread = 10

    def worker(thread_idx: int) -> None:
        for i in range(items_per_thread):
            inc_id = f"inc_t{thread_idx}_{i}"
            cache.enqueue(create_dummy_incident(inc_id, timestamp=1000 + i))

    threads: list[threading.Thread] = []
    for t_idx in range(num_threads):
        t = threading.Thread(target=worker, args=(t_idx,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert cache.count() == num_threads * items_per_thread
    cache.close()

