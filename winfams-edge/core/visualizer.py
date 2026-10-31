"""HUD and computer vision annotation renderer for WinFams Edge preview."""

from __future__ import annotations

import cv2
import numpy as np

from config import settings
from core.detector import DetectionResult
from schemas.payload import DeviceStatus

# Key landmark indices in MediaPipe Face Mesh
LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
LIPS_INDICES = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291]


def _draw_hud_bar(
    frame: np.ndarray,
    label: str,
    value: float,
    threshold: float,
    x: int,
    y: int,
    width: int = 140,
    height: int = 14,
) -> None:
    """Draw a progress bar with label and threshold marker."""
    cv2.putText(
        frame,
        f"{label}: {int(value * 100)}%",
        (x, y - 4),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (230, 230, 230),
        1,
        cv2.LINE_AA,
    )
    # Background bar
    cv2.rectangle(frame, (x, y), (x + width, y + height), (40, 40, 40), -1)
    # Fill bar
    fill_w = int(min(max(value, 0.0), 1.0) * width)
    fill_color = (0, 220, 0)
    if value >= threshold:
        fill_color = (0, 0, 255)
    elif value >= threshold * 0.7:
        fill_color = (0, 165, 255)

    cv2.rectangle(frame, (x, y), (x + fill_w, y + height), fill_color, -1)
    # Threshold indicator line
    thresh_x = x + int(threshold * width)
    cv2.line(frame, (thresh_x, y - 2), (thresh_x, y + height + 2), (0, 255, 255), 1)
    cv2.rectangle(frame, (x, y), (x + width, y + height), (120, 120, 120), 1)


def draw_driver_hud(
    frame: np.ndarray,
    status: DeviceStatus,
    detection: DetectionResult | None = None,
) -> np.ndarray:
    """Render facial landmarks, bounding box, and safety telemetry HUD onto the frame."""
    h, w = frame.shape[:2]

    # Status theme colors (BGR)
    color = (0, 220, 0)  # Green for NORMAL
    if status.state == "WARNING_FATIGUE":
        color = (0, 165, 255)  # Orange
    elif status.state == "CRITICAL_DROWSY":
        color = (0, 0, 255)  # Red

    # 1. Draw Facial Landmarks & Bounding Box if detected
    if detection is not None and detection.face_landmarks:
        pts = np.array(detection.face_landmarks, dtype=np.int32)
        x_min, y_min = np.min(pts, axis=0)
        x_max, y_max = np.max(pts, axis=0)

        # Pad bounding box slightly
        pad_x = int((x_max - x_min) * 0.1)
        pad_y = int((y_max - y_min) * 0.1)
        bx1, by1 = max(0, x_min - pad_x), max(0, y_min - pad_y)
        bx2, by2 = min(w - 1, x_max + pad_x), min(h - 1, y_max + pad_y)

        # Draw semi-transparent or cornered bounding box
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), color, 2)

        # Draw corner accents
        c_len = min(20, (bx2 - bx1) // 4)
        cv2.line(frame, (bx1, by1), (bx1 + c_len, by1), (255, 255, 255), 2)
        cv2.line(frame, (bx1, by1), (bx1, by1 + c_len), (255, 255, 255), 2)
        cv2.line(frame, (bx2, by2), (bx2 - c_len, by2), (255, 255, 255), 2)
        cv2.line(frame, (bx2, by2), (bx2, by2 - c_len), (255, 255, 255), 2)

        # Draw contours for left eye, right eye, and lips
        for indices in (LEFT_EYE_INDICES, RIGHT_EYE_INDICES):
            eye_pts = np.array([detection.face_landmarks[i] for i in indices], dtype=np.int32)
            cv2.polylines(frame, [eye_pts], isClosed=True, color=(0, 255, 255), thickness=1)

        lips_pts = np.array([detection.face_landmarks[i] for i in LIPS_INDICES], dtype=np.int32)
        cv2.polylines(frame, [lips_pts], isClosed=True, color=(255, 200, 0), thickness=1)

    # 2. Top-Left HUD Card: Driver State Badge
    cv2.rectangle(frame, (12, 12), (260, 52), (20, 20, 20), -1)
    cv2.rectangle(frame, (12, 12), (260, 52), color, 2)
    cv2.putText(
        frame,
        f"STATUS: {status.state}",
        (22, 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
        cv2.LINE_AA,
    )

    # 3. Telemetry Confidence Bars
    drowsy_val = detection.drowsy_confidence if detection else status.drowsy_confidence
    yawn_val = detection.yawn_confidence if detection else status.yawn_confidence

    _draw_hud_bar(frame, "Mata (Blink)", drowsy_val, settings.BLINK_THRESHOLD, 14, 76)
    _draw_hud_bar(frame, "Mulut (Yawn)", yawn_val, settings.YAWN_THRESHOLD, 14, 112)

    # 4. Bottom Telemetry Bar: Speed & GPS Status
    speed = status.location.speed_kmh if status.location else 0.0
    has_gps = status.location.lat is not None if status.location else False
    gps_str = f"GPS: {status.location.lat:.4f}, {status.location.lng:.4f}" if has_gps else "GPS: Searching..."

    cv2.rectangle(frame, (0, h - 30), (w, h), (15, 15, 15), -1)
    cv2.putText(
        frame,
        f"Speed: {speed:.1f} km/h  |  {gps_str}",
        (16, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )

    return frame

