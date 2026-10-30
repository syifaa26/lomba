"""SQLite local cache providing an offline queue for fatigue incidents.

Stores un-synced FatigueIncident payloads locally when network connectivity
is lost, enabling reliable FIFO synchronization once connection is restored.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any

from config import settings
from schemas.payload import FatigueIncident

logger = logging.getLogger(__name__)


class LocalCache:
    """Thread-safe SQLite persistent offline queue for FatigueIncident records."""

    def __init__(self, db_path: Path | str = settings.SQLITE_DB_PATH) -> None:
        """Initialize SQLite database and ensure tables exist."""
        self.db_path: Path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock: threading.Lock = threading.Lock()

        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=10.0,
        )
        self._conn.row_factory = sqlite3.Row
        self._init_db()
        logger.info("LocalCache initialized at: %s", self.db_path)

    def _init_db(self) -> None:
        """Create the offline queue schema if not already present."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS offline_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT UNIQUE NOT NULL,
                    device_id TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_offline_timestamp
                ON offline_incidents (timestamp ASC);
                """
            )
            self._conn.commit()

    def enqueue(self, incident: FatigueIncident) -> bool:
        """Add a FatigueIncident to the persistent queue.

        Args:
            incident: The fatigue incident to be stored.

        Returns:
            True if inserted successfully, False otherwise.
        """
        query = """
            INSERT OR IGNORE INTO offline_incidents (
                incident_id, device_id, timestamp, payload_json
            ) VALUES (?, ?, ?, ?);
        """
        payload_json = incident.to_json()
        with self._lock:
            try:
                cursor = self._conn.cursor()
                cursor.execute(
                    query,
                    (
                        incident.incident_id,
                        incident.device_id,
                        incident.timestamp,
                        payload_json,
                    ),
                )
                self._conn.commit()
                inserted = cursor.rowcount > 0
                if inserted:
                    logger.debug("Enqueued incident %s into LocalCache", incident.incident_id)
                return inserted
            except sqlite3.Error as exc:
                logger.error("Failed to enqueue incident %s: %s", incident.incident_id, exc)
                return False

    def peek(self, limit: int = 50) -> list[FatigueIncident]:
        """Fetch the oldest un-synced incidents without removing them.

        Args:
            limit: Maximum number of incidents to return.

        Returns:
            List of FatigueIncident objects ordered from oldest to newest.
        """
        query = """
            SELECT payload_json FROM offline_incidents
            ORDER BY timestamp ASC, id ASC
            LIMIT ?;
        """
        results: list[FatigueIncident] = []
        with self._lock:
            try:
                cursor = self._conn.cursor()
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                for row in rows:
                    results.append(FatigueIncident.from_json(row["payload_json"]))
            except (sqlite3.Error, ValueError) as exc:
                logger.error("Failed to read from LocalCache: %s", exc)
        return results

    def dequeue(self, incident_ids: list[str]) -> int:
        """Remove successfully uploaded incidents from the offline queue.

        Args:
            incident_ids: List of incident_id strings to remove.

        Returns:
            The number of rows deleted.
        """
        if not incident_ids:
            return 0

        placeholders = ",".join("?" for _ in incident_ids)
        query = f"DELETE FROM offline_incidents WHERE incident_id IN ({placeholders});"

        with self._lock:
            try:
                cursor = self._conn.cursor()
                cursor.execute(query, incident_ids)
                self._conn.commit()
                deleted_count = cursor.rowcount
                logger.info("Dequeued %d synced incidents from LocalCache", deleted_count)
                return deleted_count
            except sqlite3.Error as exc:
                logger.error("Failed to dequeue incidents: %s", exc)
                return 0

    def count(self) -> int:
        """Return the current total number of queued incidents."""
        with self._lock:
            try:
                cursor = self._conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM offline_incidents;")
                row = cursor.fetchone()
                return int(row[0]) if row else 0
            except sqlite3.Error as exc:
                logger.error("Failed to count items in LocalCache: %s", exc)
                return 0

    def clear(self) -> None:
        """Delete all queued records in the table."""
        with self._lock:
            try:
                cursor = self._conn.cursor()
                cursor.execute("DELETE FROM offline_incidents;")
                self._conn.commit()
                logger.info("LocalCache cleared.")
            except sqlite3.Error as exc:
                logger.error("Failed to clear LocalCache: %s", exc)

    def close(self) -> None:
        """Close SQLite database connection cleanly."""
        with self._lock:
            try:
                self._conn.close()
                logger.info("LocalCache connection closed.")
            except Exception as exc:
                logger.debug("Error closing SQLite connection: %s", exc)

    def __enter__(self) -> LocalCache:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

