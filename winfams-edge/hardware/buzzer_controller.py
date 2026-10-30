"""Non-blocking buzzer controller for driver drowsiness and fatigue alerts.

Provides rapid and slow acoustic warning patterns. Automatically falls back
to mock mode when executing on PC/laptop without Raspberry Pi GPIO pins.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from config import settings

logger = logging.getLogger(__name__)


class MockBuzzerHardware:
    """Mock buzzer hardware driver for testing on non-Raspberry Pi environments."""

    def __init__(self, pin: int) -> None:
        self.pin: int = pin
        self.is_active: bool = False
        self.toggle_count: int = 0
        logger.info("Initialized MockBuzzerHardware on simulated GPIO pin %d", pin)

    def on(self) -> None:
        """Simulate buzzer sounding."""
        self.is_active = True
        self.toggle_count += 1
        logger.debug("[MOCK BUZZER PIN %d] ON (BEEP)", self.pin)

    def off(self) -> None:
        """Simulate buzzer silence."""
        self.is_active = False
        logger.debug("[MOCK BUZZER PIN %d] OFF", self.pin)

    def close(self) -> None:
        """Release mock resources."""
        self.off()
        logger.info("MockBuzzerHardware on pin %d closed.", self.pin)


class BuzzerController:
    """Thread-safe, non-blocking buzzer controller for active audible alerts."""

    def __init__(self, pin: int = settings.BUZZER_PIN, force_mock: bool = False) -> None:
        """Initialize buzzer driver on specified GPIO pin with mock fallback."""
        self.pin: int = pin
        self.is_mock: bool = force_mock
        self._buzzer: Any = None

        if not force_mock:
            try:
                from gpiozero import Buzzer  # type: ignore

                self._buzzer = Buzzer(pin)
                logger.info("Native gpiozero.Buzzer initialized on GPIO pin %d", pin)
            except Exception as exc:
                logger.warning(
                    "GPIO hardware unavailable (%s). Falling back to MockBuzzerHardware.",
                    exc,
                )
                self.is_mock = True
                self._buzzer = MockBuzzerHardware(pin)
        else:
            self._buzzer = MockBuzzerHardware(pin)

        self._stop_event: threading.Event = threading.Event()
        self._worker_thread: threading.Thread | None = None
        self._lock: threading.Lock = threading.Lock()

    def trigger_critical(self, count: int = 6, on_sec: float = 0.12, off_sec: float = 0.10) -> None:
        """Trigger rapid pulse alarm for CRITICAL_DROWSY in a non-blocking thread."""
        logger.warning(
            "Triggering CRITICAL alarm pattern (count=%d, on=%.2fs, off=%.2fs)",
            count,
            on_sec,
            off_sec,
        )
        self._start_alert_pattern(count=count, on_sec=on_sec, off_sec=off_sec)

    def trigger_warning(self, count: int = 3, on_sec: float = 0.35, off_sec: float = 0.30) -> None:
        """Trigger slow pulse alarm for WARNING_FATIGUE in a non-blocking thread."""
        logger.info(
            "Triggering WARNING alarm pattern (count=%d, on=%.2fs, off=%.2fs)",
            count,
            on_sec,
            off_sec,
        )
        self._start_alert_pattern(count=count, on_sec=on_sec, off_sec=off_sec)

    def _start_alert_pattern(self, count: int, on_sec: float, off_sec: float) -> None:
        """Launch background worker thread to execute audible pulse pattern."""
        with self._lock:
            self.stop()
            self._stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._beep_worker,
                args=(count, on_sec, off_sec),
                name="BuzzerAlertWorker",
                daemon=True,
            )
            self._worker_thread.start()

    def _beep_worker(self, count: int, on_sec: float, off_sec: float) -> None:
        """Background worker pulsing buzzer on and off without blocking main loop."""
        for _ in range(count):
            if self._stop_event.is_set():
                break

            self._buzzer.on()
            if self._sleep_cancellable(on_sec):
                break

            self._buzzer.off()
            if self._sleep_cancellable(off_sec):
                break

        # Ensure buzzer is off after pattern completes
        self._buzzer.off()

    def _sleep_cancellable(self, duration_sec: float) -> bool:
        """Wait for duration or until stop_event is signaled. Returns True if stopped."""
        return self._stop_event.wait(timeout=duration_sec)

    def stop(self) -> None:
        """Immediately interrupt any active alarm pattern and silence buzzer."""
        self._stop_event.set()
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
            self._worker_thread = None

        if self._buzzer is not None:
            self._buzzer.off()

    @property
    def is_alerting(self) -> bool:
        """Check if an alarm pattern is actively sounding."""
        return self._worker_thread is not None and self._worker_thread.is_alive()

    def close(self) -> None:
        """Stop worker and release buzzer hardware."""
        self.stop()
        if self._buzzer is not None:
            self._buzzer.close()
            self._buzzer = None
        logger.info("BuzzerController closed.")

    def __enter__(self) -> BuzzerController:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

