"""Multithreaded camera stream reader for real-time video acquisition.

Prevents buffer lag on Raspberry Pi / Edge devices by continuously grabbing
frames in a background daemon thread.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraStream:
    """Thread-safe camera stream reading frames in a separate daemon thread."""

    def __init__(
        self,
        src: int | str = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
        reconnect_interval_sec: float = 2.0,
    ) -> None:
        """Initialize camera stream parameters.

        Args:
            src: Device camera index (int) or video source path (str).
            width: Desired capture frame width.
            height: Desired capture frame height.
            fps: Desired capture frames per second.
            reconnect_interval_sec: Seconds to wait before attempting reconnect.
        """
        self.src: int | str = src
        self.width: int = width
        self.height: int = height
        self.fps: int = fps
        self.reconnect_interval_sec: float = reconnect_interval_sec

        self._cap: cv2.VideoCapture | None = None
        self._frame: np.ndarray | None = None
        self._grabbed: bool = False
        self._running: bool = False

        self._lock: threading.Lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def _open_capture(self) -> bool:
        """Open VideoCapture and set resolution parameters."""
        if self._cap is not None:
            self._cap.release()

        logger.info("Opening camera stream on source: %s", self.src)
        self._cap = cv2.VideoCapture(self.src)

        if not self._cap.isOpened():
            logger.warning("Failed to open camera on source: %s", self.src)
            return False

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(self.width))
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self.height))
        self._cap.set(cv2.CAP_PROP_FPS, float(self.fps))

        # Read initial warm-up frame
        grabbed, frame = self._cap.read()
        if grabbed and frame is not None:
            with self._lock:
                self._grabbed = True
                self._frame = frame
            # Rewind to start if reading from video file
            if isinstance(self.src, str):
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            logger.info("Camera stream successfully opened and warmed up.")
            return True

        logger.warning("Camera opened but failed to grab initial frame.")
        return False

    def start(self) -> CameraStream:
        """Start the background reading thread.

        Returns:
            Self instance for chaining.
        """
        if self._running:
            logger.warning("CameraStream thread is already running.")
            return self

        self._running = True
        self._open_capture()

        self._thread = threading.Thread(
            target=self._capture_loop,
            name="CameraStreamWorker",
            daemon=True,
        )
        self._thread.start()
        logger.info("CameraStream worker thread started.")
        return self

    def _capture_loop(self) -> None:
        """Continuously grab frames from the camera in a daemon thread."""
        delay_sec = 1.0 / max(1, self.fps) if isinstance(self.src, str) else 0.001

        while self._running:
            if self._cap is None or not self._cap.isOpened():
                logger.warning(
                    "Camera not connected. Retrying in %.1fs...",
                    self.reconnect_interval_sec,
                )
                time.sleep(self.reconnect_interval_sec)
                self._open_capture()
                continue

            grabbed, frame = self._cap.read()

            if not grabbed or frame is None:
                # Rewind if reading video file for simulation / testing
                if isinstance(self.src, str):
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                time.sleep(0.01)
                continue

            with self._lock:
                self._grabbed = True
                self._frame = frame

            # Pace playback only if reading from static video file
            if delay_sec > 0.001:
                time.sleep(delay_sec)

    def read(self) -> tuple[bool, np.ndarray | None]:
        """Thread-safely retrieve the latest frame.

        Returns:
            A tuple of (grabbed, frame). If no frame is available, (False, None).
        """
        with self._lock:
            if not self._grabbed or self._frame is None:
                return False, None
            return True, self._frame.copy()

    @property
    def is_running(self) -> bool:
        """Check if background worker thread is active."""
        return self._running

    def stop(self) -> None:
        """Stop background worker thread and release camera resources."""
        logger.info("Stopping CameraStream...")
        self._running = False

        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            self._thread = None

        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
            self._grabbed = False
            self._frame = None

        logger.info("CameraStream stopped and resources released.")

    def __enter__(self) -> CameraStream:
        """Support context manager syntax."""
        return self.start()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Ensure cleanup when exiting context."""
        self.stop()
