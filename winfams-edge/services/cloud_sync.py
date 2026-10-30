"""Firebase cloud sync service handling realtime telemetry, incidents, and FCM.

Runs in a dedicated background worker thread to ensure zero blocking on
the edge vision loop. Seamlessly buffers to LocalCache SQLite on disconnection
and flushes queued incidents once connectivity is restored.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Any

from config import settings
from schemas.payload import DeviceStatus, FatigueIncident
from services.local_cache import LocalCache

logger = logging.getLogger(__name__)


class CloudSyncService:
    """Asynchronous cloud synchronization worker for Firebase and offline queue."""

    def __init__(
        self,
        local_cache: LocalCache | None = None,
        credentials_path: Path | str = settings.FIREBASE_CREDENTIALS_PATH,
        rtdb_url: str = settings.FIREBASE_RTDB_URL,
        telemetry_interval_sec: float = settings.TELEMETRY_INTERVAL_SEC,
        force_mock: bool = False,
    ) -> None:
        """Initialize sync service and Firebase Admin SDK with mock fallback."""
        self.local_cache: LocalCache = local_cache or LocalCache()
        self.credentials_path: Path = Path(credentials_path)
        self.rtdb_url: str = rtdb_url
        self.telemetry_interval_sec: float = telemetry_interval_sec
        self.is_mock: bool = force_mock
        self.simulate_offline: bool = False

        self._latest_status: DeviceStatus | None = None
        self._incident_queue: queue.Queue[FatigueIncident] = queue.Queue()
        self._lock: threading.Lock = threading.Lock()
        self._stop_event: threading.Event = threading.Event()
        self._worker_thread: threading.Thread | None = None
        self._last_telemetry_time: float = 0.0

        # Mock storage for testing
        self.mock_statuses: list[dict[str, Any]] = []
        self.mock_incidents: list[dict[str, Any]] = []
        self.mock_fcm_messages: list[dict[str, Any]] = []

        if not force_mock and self.credentials_path.exists():
            try:
                import firebase_admin
                from firebase_admin import credentials

                if not firebase_admin._apps:
                    cred = credentials.Certificate(str(self.credentials_path))
                    firebase_admin.initialize_app(cred, {"databaseURL": self.rtdb_url})
                logger.info("Firebase Admin SDK initialized successfully.")
            except Exception as exc:
                logger.warning("Firebase init failed (%s). Falling back to mock sync.", exc)
                self.is_mock = True
        else:
            self.is_mock = True
            logger.info("CloudSyncService operating in mock mode.")

    def start(self) -> None:
        """Start asynchronous cloud synchronization worker thread."""
        with self._lock:
            if self._worker_thread is not None and self._worker_thread.is_alive():
                return
            self._stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._sync_worker,
                name="CloudSyncWorker",
                daemon=True,
            )
            self._worker_thread.start()
            logger.info("CloudSyncService background worker started.")

    def stop(self) -> None:
        """Signal worker thread to stop and wait for clean shutdown."""
        self._stop_event.set()
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
            self._worker_thread = None
            logger.info("CloudSyncService background worker stopped.")

    def update_status(self, status: DeviceStatus) -> None:
        """Update current device telemetry snapshot (thread-safe, non-blocking)."""
        with self._lock:
            self._latest_status = status

    def report_incident(self, incident: FatigueIncident) -> None:
        """Enqueue incident for asynchronous cloud transmission and FCM dispatch."""
        self._incident_queue.put(incident)
        logger.info("Queued incident %s for cloud sync", incident.incident_id)

    def upload_status(self, status: DeviceStatus) -> bool:
        """Transmit DeviceStatus to Firebase Realtime Database."""
        if self.simulate_offline:
            return False

        if self.is_mock:
            self.mock_statuses.append(status.to_dict())
            return True

        try:
            from firebase_admin import db

            ref = db.reference(f"devices/{status.device_id}/status")
            ref.set(status.to_dict())
            logger.debug("DeviceStatus published to RTDB for %s", status.device_id)
            return True
        except Exception as exc:
            logger.error("Failed to upload status to RTDB: %s", exc)
            return False

    def upload_incident(self, incident: FatigueIncident) -> bool:
        """Store incident in Firestore and broadcast high-priority FCM notification."""
        if self.simulate_offline:
            return False

        if self.is_mock:
            self.mock_incidents.append(incident.to_dict())
            self.mock_fcm_messages.append(
                {
                    "topic": f"family_{incident.family_group_id}",
                    "type": incident.type,
                    "incident_id": incident.incident_id,
                }
            )
            logger.info("Mock cloud upload & FCM succeeded for %s", incident.incident_id)
            return True

        try:
            from firebase_admin import firestore, messaging

            # 1. Firestore persistence
            fs_db = firestore.client()
            fs_db.collection("incidents").document(incident.incident_id).set(
                incident.to_dict()
            )

            # 2. FCM Broadcast
            title = (
                "PERINGATAN KRITIS: Kantuk Berat!"
                if incident.type == "CRITICAL_DROWSY"
                else "Peringatan Kelelahan Pengemudi"
            )
            body = (
                f"Pengemudi ({incident.driver_uid}) mengalami {incident.type} "
                f"pada kecepatan {incident.location.speed_kmh} km/h."
            )
            msg = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={
                    "incident_id": incident.incident_id,
                    "type": incident.type,
                    "device_id": incident.device_id,
                    "speed_kmh": str(incident.location.speed_kmh),
                },
                topic=f"family_{incident.family_group_id}",
            )
            messaging.send(msg)
            logger.info("Incident %s stored in Firestore and FCM sent.", incident.incident_id)
            return True
        except Exception as exc:
            logger.error("Failed to upload incident %s: %s", incident.incident_id, exc)
            return False

    def flush_offline_queue(self, batch_size: int = 20) -> int:
        """Upload cached incidents from local SQLite queue to cloud."""
        if self.simulate_offline:
            return 0

        cached = self.local_cache.peek(limit=batch_size)
        if not cached:
            return 0

        synced_ids: list[str] = []
        for inc in cached:
            if self.upload_incident(inc):
                synced_ids.append(inc.incident_id)
            else:
                break

        if synced_ids:
            return self.local_cache.dequeue(synced_ids)
        return 0

    def _sync_worker(self) -> None:
        """Background worker handling periodic telemetry and offline queue flushing."""
        while not self._stop_event.is_set():
            # 1. Process pending immediate incidents
            while not self._incident_queue.empty():
                try:
                    inc = self._incident_queue.get_nowait()
                except queue.Empty:
                    break

                if not self.upload_incident(inc):
                    logger.warning("Cloud upload failed. Caching %s offline.", inc.incident_id)
                    self.local_cache.enqueue(inc)
                self._incident_queue.task_done()

            # 2. Periodic RTDB Telemetry and Queue Flush
            now = time.time()
            if now - self._last_telemetry_time >= self.telemetry_interval_sec:
                self._last_telemetry_time = now
                with self._lock:
                    current_status = self._latest_status

                if current_status is not None:
                    self.upload_status(current_status)

                flushed = self.flush_offline_queue()
                if flushed > 0:
                    logger.info("Flushed %d offline incidents to cloud.", flushed)

            self._stop_event.wait(timeout=0.05)

    def __enter__(self) -> CloudSyncService:
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()
