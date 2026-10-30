"""FastAPI Edge client and asynchronous background sync worker.

Provides non-blocking HTTP dispatch for telemetry heartbeats and fatigue incidents
with automatic local SQLite queue fallback during network loss.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Any

import requests

from config import settings
from schemas.payload import FatigueIncident, HeartbeatPayload, IncidentPayload
from services.local_cache import LocalCache

logger = logging.getLogger("winfams.edge.sync")


class ApiClient:
    """HTTP Client communicating with WinFams FastAPI edge ingestion endpoints."""

    def __init__(
        self,
        base_url: str = settings.API_BASE_URL,
        api_key: str = settings.DEVICE_API_KEY,
        timeout: float = 3.0,
    ) -> None:
        self.base_url: str = base_url.rstrip("/")
        self.api_key: str = api_key
        self.timeout: float = timeout
        self.session: requests.Session = requests.Session()
        self.session.headers.update(
            {
                "X-Device-API-Key": self.api_key,
                "Content-Type": "application/json",
            }
        )

    def send_heartbeat(self, payload: HeartbeatPayload) -> bool:
        """Send periodic telemetry heartbeat to POST /api/v1/edge/heartbeat."""
        url = f"{self.base_url}/api/v1/edge/heartbeat"
        try:
            resp = self.session.post(url, json=payload.to_dict(), timeout=self.timeout)
            return resp.status_code == 200
        except Exception as exc:
            logger.debug("Failed to send heartbeat to %s: %s", url, exc)
            return False

    def send_incident(self, incident: IncidentPayload | FatigueIncident) -> bool:
        """Send fatigue alert to POST /api/v1/edge/incidents."""
        url = f"{self.base_url}/api/v1/edge/incidents"
        if isinstance(incident, FatigueIncident):
            payload = incident.to_incident_payload()
        else:
            payload = incident

        try:
            resp = self.session.post(url, json=payload.to_dict(), timeout=self.timeout)
            return resp.status_code == 201
        except Exception as exc:
            logger.debug("Failed to send incident to %s: %s", url, exc)
            return False

    def is_online(self) -> bool:
        """Check API connectivity via health endpoint."""
        url = f"{self.base_url}/health"
        try:
            resp = self.session.get(url, timeout=1.5)
            return resp.status_code == 200
        except Exception:
            return False


class BackgroundSyncWorker:
    """Non-blocking background worker managing heartbeats, alerts, and SQLite cache."""

    def __init__(
        self,
        api_client: ApiClient | None = None,
        local_cache: LocalCache | None = None,
        heartbeat_interval_sec: float = settings.TELEMETRY_INTERVAL_SEC,
    ) -> None:
        self.api_client: ApiClient = api_client or ApiClient()
        self.local_cache: LocalCache = local_cache or LocalCache()
        self.heartbeat_interval: float = heartbeat_interval_sec

        self._queue: queue.Queue[FatigueIncident | IncidentPayload] = queue.Queue()
        self._latest_heartbeat: HeartbeatPayload | None = None
        self._lock: threading.Lock = threading.Lock()
        self._stop_event: threading.Event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the background synchronization thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="BackgroundSyncWorker", daemon=True
        )
        self._thread.start()
        logger.info("BackgroundSyncWorker thread started.")

    def stop(self, timeout: float = 2.0) -> None:
        """Signal worker thread to stop and wait for join."""
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        logger.info("BackgroundSyncWorker thread stopped.")

    def enqueue_incident(self, incident: FatigueIncident | IncidentPayload) -> None:
        """Push an incident into the non-blocking queue (safe for OpenCV main loop)."""
        self._queue.put_nowait(incident)

    def update_telemetry(self, payload: HeartbeatPayload) -> None:
        """Update the latest telemetry heartbeat payload thread-safely."""
        with self._lock:
            self._latest_heartbeat = payload

    def flush_offline_queue(self, limit: int = 10) -> int:
        """Upload cached offline incidents to FastAPI Backend."""
        items = self.local_cache.peek(limit=limit)
        if not items:
            return 0

        synced_ids: list[str] = []
        for item in items:
            if self.api_client.send_incident(item):
                synced_ids.append(item.incident_id)
            else:
                break  # Stop flush on network drop

        if synced_ids:
            self.local_cache.dequeue(synced_ids)
            logger.info("Flushed %d offline incidents to API", len(synced_ids))

        return len(synced_ids)

    def _run(self) -> None:
        """Main background worker execution loop."""
        last_hb_time = 0.0

        while not self._stop_event.is_set():
            # 1. Drain pending real-time incidents from memory queue
            while not self._queue.empty():
                try:
                    inc = self._queue.get_nowait()
                except queue.Empty:
                    break

                sent = self.api_client.send_incident(inc)
                if not sent:
                    # Persist to local SQLite queue if offline
                    if isinstance(inc, FatigueIncident):
                        self.local_cache.enqueue(inc)
                    else:
                        compat_inc = FatigueIncident(
                            incident_id=f"inc_{int(time.time() * 1000)}",
                            device_id=inc.device_uid,
                            driver_uid=settings.DRIVER_UID,
                            family_group_id=settings.FAMILY_GROUP_ID,
                            type=inc.incident_type,
                            confidence_score=inc.confidence_score,
                            duration_seconds=inc.duration_seconds,
                            location=inc.location,
                            timestamp=inc.recorded_at,
                        )
                        self.local_cache.enqueue(compat_inc)

            # 2. Check heartbeat timer
            now = time.time()
            if now - last_hb_time >= self.heartbeat_interval:
                with self._lock:
                    hb = self._latest_heartbeat
                if hb is not None:
                    hb_success = self.api_client.send_heartbeat(hb)
                    if hb_success:
                        self.flush_offline_queue()
                last_hb_time = now

            self._stop_event.wait(0.2)

