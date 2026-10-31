"""Lightweight HTTP MJPEG streaming and live telemetry web server for WinFams Edge.

Provides an in-browser live cockpit view accessible over LAN (e.g. from laptop
or smartphone) without requiring third-party web frameworks or GUI displays.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import cv2
import numpy as np

from config import settings
from schemas.payload import DeviceStatus
from services.web_template import DASHBOARD_HTML

logger = logging.getLogger("winfams.edge.web")


class WebStreamer:
    """Thread-safe MJPEG streamer and web dashboard server."""

    def __init__(self, host: str = "0.0.0.0", port: int = 5000) -> None:
        self.host: str = host
        self.port: int = port
        self.latest_jpeg: bytes | None = None
        self.latest_status: dict[str, Any] = {}
        self.condition: threading.Condition = threading.Condition()

        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._running: bool = False

    def update(
        self,
        frame: np.ndarray | None,
        status: DeviceStatus | None,
        buzzer_active: bool = False,
        detection: Any = None,
    ) -> None:
        """Update live frame and telemetry data for web viewers."""
        if frame is None or status is None:
            return

        annotated = frame.copy()
        if detection is not None and getattr(detection, "face_landmarks", None):
            from core.visualizer import draw_driver_hud
            annotated = draw_driver_hud(annotated, status, detection)
        else:
            self._draw_hud(annotated, status, buzzer_active)

        ret, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ret:
            return

        with self.condition:
            self.latest_jpeg = buffer.tobytes()
            self.latest_status = {
                "device_id": status.device_id,
                "state": status.state,
                "drowsy_confidence": status.drowsy_confidence,
                "yawn_confidence": status.yawn_confidence,
                "buzzer_active": buzzer_active,
                "location": {
                    "lat": status.location.lat,
                    "lng": status.location.lng,
                    "speed_kmh": status.location.speed_kmh,
                },
                "last_updated": status.last_updated,
            }
            self.condition.notify_all()

    def _draw_hud(self, frame: np.ndarray, status: DeviceStatus, buzzer_active: bool) -> None:
        """Render HUD indicators on frame for direct stream viewers."""
        h, w = frame.shape[:2]
        # Top banner overlay
        color = (0, 200, 0)
        state_text = f"STATE: {status.state}"
        if status.state == "CRITICAL_DROWSY":
            color = (0, 0, 255)
            state_text = "! CRITICAL DROWSY !"
        elif status.state == "WARNING_FATIGUE":
            color = (0, 165, 255)
            state_text = "WARNING: YAWN"

        cv2.rectangle(frame, (10, 10), (w - 10, 48), (20, 20, 20), -1)
        cv2.rectangle(frame, (10, 10), (w - 10, 48), color, 2)
        cv2.putText(frame, state_text, (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Telemetry overlay at bottom
        cv2.rectangle(frame, (10, h - 55), (w - 10, h - 10), (20, 20, 20), -1)
        drowsy_str = f"Eye Blink: {status.drowsy_confidence:.2f}"
        yawn_str = f"Yawn: {status.yawn_confidence:.2f}"
        buzzer_str = "ALARM: ON" if buzzer_active else "Buzzer: OK"
        cv2.putText(frame, f"{drowsy_str}  |  {yawn_str}  |  {buzzer_str}", (20, h - 26), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)

    def start(self) -> None:
        """Start the background HTTP server."""
        if self._running:
            return

        streamer = self

        class StreamHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                return  # Suppress console HTTP log spam

            def do_GET(self) -> None:
                if self.path in ("/", "/index.html"):
                    content = DASHBOARD_HTML.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                elif self.path == "/api/status":
                    data = json.dumps(streamer.latest_status).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                elif self.path == "/video_feed":
                    self.send_response(200)
                    self.send_header("Age", "0")
                    self.send_header("Cache-Control", "no-cache, private")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                    self.end_headers()
                    try:
                        while streamer._running:
                            with streamer.condition:
                                streamer.condition.wait(timeout=1.0)
                                frame_bytes = streamer.latest_jpeg
                            if frame_bytes:
                                self.wfile.write(b"--frame\r\n")
                                self.send_header("Content-Type", "image/jpeg")
                                self.send_header("Content-Length", str(len(frame_bytes)))
                                self.end_headers()
                                self.wfile.write(frame_bytes)
                                self.wfile.write(b"\r\n")
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                else:
                    self.send_error(404, "Not Found")

        try:
            self._server = ThreadingHTTPServer((self.host, self.port), StreamHandler)
            self._running = True
            self._thread = threading.Thread(
                target=self._server.serve_forever,
                name="WebStreamerWorker",
                daemon=True,
            )
            self._thread.start()
            logger.info("Web Streamer UI active at: http://%s:%d", self.host, self.port)
        except Exception as exc:
            logger.error("Failed to start WebStreamer on port %d: %s", self.port, exc)

    def stop(self) -> None:
        """Stop HTTP server and clean up worker thread."""
        if not self._running:
            return
        self._running = False
        with self.condition:
            self.condition.notify_all()
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        logger.info("Web Streamer UI stopped.")

