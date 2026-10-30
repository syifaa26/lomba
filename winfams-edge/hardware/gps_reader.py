"""GPS serial reader thread parsing NMEA sentences for real-time telemetry.

Reads NMEA sentences ($GPGGA, $GPRMC) from a hardware UART serial port
using pyserial and pynmea2. Automatically falls back to a thread-safe
mock mode when running on environments without physical GPS hardware.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import pynmea2
import serial

from config import settings
from schemas.payload import LocationData

logger = logging.getLogger(__name__)


class GPSReader:
    """Thread-safe GPS receiver reading NMEA frames asynchronously."""

    def __init__(
        self,
        port: str = settings.GPS_SERIAL_PORT,
        baudrate: int = settings.GPS_BAUDRATE,
        timeout: float = settings.GPS_TIMEOUT,
        force_mock: bool = False,
        mock_lat: float = -1.265386,
        mock_lng: float = 116.831200,
        mock_speed_kmh: float = 0.0,
        mock_heading: float = 0.0,
    ) -> None:
        """Initialize GPS reader with serial port or mock fallback."""
        self.port: str = port
        self.baudrate: int = baudrate
        self.timeout: float = timeout
        self.is_mock: bool = force_mock
        self._serial: serial.Serial | None = None
        self._lock: threading.Lock = threading.Lock()
        self._stop_event: threading.Event = threading.Event()
        self._worker_thread: threading.Thread | None = None
        self._has_fix: bool = False

        if not force_mock:
            try:
                self._serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                )
                logger.info("GPS serial interface opened on %s at %d baud", port, baudrate)
            except (serial.SerialException, FileNotFoundError, OSError) as exc:
                logger.warning(
                    "GPS serial port %s unavailable (%s). Falling back to mock GPS mode.",
                    port,
                    exc,
                )
                self.is_mock = True

        if self.is_mock:
            self._location: LocationData = LocationData(
                lat=mock_lat,
                lng=mock_lng,
                speed_kmh=mock_speed_kmh,
                heading=mock_heading,
            )
            self._has_fix = True
            logger.info("Mock GPS active at (lat=%.6f, lng=%.6f)", mock_lat, mock_lng)
        else:
            self._location = LocationData()

    def start(self) -> None:
        """Start background polling thread to read GPS frames."""
        with self._lock:
            if self._worker_thread is not None and self._worker_thread.is_alive():
                return
            self._stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._worker,
                name="GPSReaderWorker",
                daemon=True,
            )
            self._worker_thread.start()
            logger.info("GPSReader worker thread started.")

    def stop(self) -> None:
        """Signal worker thread to terminate and wait for completion."""
        self._stop_event.set()
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
            self._worker_thread = None
            logger.info("GPSReader worker thread stopped.")

    def close(self) -> None:
        """Stop background thread and close serial connection."""
        self.stop()
        if self._serial is not None and self._serial.is_open:
            try:
                self._serial.close()
            except Exception as exc:
                logger.debug("Error closing serial port: %s", exc)
            self._serial = None
        logger.info("GPSReader closed.")

    def get_location(self) -> LocationData:
        """Return a thread-safe copy of the latest location telemetry."""
        with self._lock:
            return LocationData(
                lat=self._location.lat,
                lng=self._location.lng,
                speed_kmh=self._location.speed_kmh,
                heading=self._location.heading,
            )

    @property
    def has_fix(self) -> bool:
        """Return True if GPS receiver currently holds a valid satellite fix."""
        with self._lock:
            return self._has_fix and self._location.lat is not None

    def set_mock_location(
        self,
        lat: float | None,
        lng: float | None,
        speed_kmh: float = 0.0,
        heading: float = 0.0,
        has_fix: bool = True,
    ) -> None:
        """Manually override telemetry for testing and simulation."""
        with self._lock:
            self._location = LocationData(
                lat=lat,
                lng=lng,
                speed_kmh=speed_kmh,
                heading=heading,
            )
            self._has_fix = has_fix

    def parse_nmea_sentence(self, sentence: str) -> bool:
        """Parse raw NMEA sentence and update internal state."""
        clean = sentence.strip()
        if not clean.startswith("$"):
            return False

        try:
            msg = pynmea2.parse(clean)
        except pynmea2.ParseError:
            return False

        with self._lock:
            sentence_type = getattr(msg, "sentence_type", None)

            if sentence_type == "GGA":
                gps_qual = int(getattr(msg, "gps_qual", 0) or 0)
                if gps_qual > 0:
                    self._location.lat = float(msg.latitude)
                    self._location.lng = float(msg.longitude)
                    self._has_fix = True
                else:
                    self._location.lat = None
                    self._location.lng = None
                    self._has_fix = False
                return True

            elif sentence_type == "RMC":
                status = getattr(msg, "status", "V")
                if status == "A":
                    self._location.lat = float(msg.latitude)
                    self._location.lng = float(msg.longitude)
                    raw_speed = getattr(msg, "spd_over_grnd", None)
                    spd_knots = float(raw_speed) if raw_speed is not None else 0.0
                    self._location.speed_kmh = round(spd_knots * 1.852, 2)
                    raw_heading = getattr(msg, "true_course", None)
                    self._location.heading = (
                        round(float(raw_heading), 2) if raw_heading is not None else 0.0
                    )
                    self._has_fix = True
                else:
                    self._location.lat = None
                    self._location.lng = None
                    self._location.speed_kmh = 0.0
                    self._has_fix = False
                return True

        return False

    def _worker(self) -> None:
        """Background thread target dispatching to serial or mock loop."""
        if self.is_mock or self._serial is None:
            self._mock_loop()
        else:
            self._serial_loop()

    def _serial_loop(self) -> None:
        """Continuously read raw lines from serial UART."""
        while not self._stop_event.is_set():
            if self._serial is None or not self._serial.is_open:
                break
            try:
                raw_bytes = self._serial.readline()
                if not raw_bytes:
                    continue
                line = raw_bytes.decode("ascii", errors="replace").strip()
                if line.startswith("$"):
                    self.parse_nmea_sentence(line)
            except (serial.SerialException, OSError) as exc:
                logger.error("Serial read error: %s. Re-attempting in 1s.", exc)
                self._stop_event.wait(timeout=1.0)
            except Exception as exc:
                logger.debug("Unexpected error in GPS serial loop: %s", exc)

    def _mock_loop(self) -> None:
        """Idle wait loop when running in mock mode."""
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=0.5)

    def __enter__(self) -> GPSReader:
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
