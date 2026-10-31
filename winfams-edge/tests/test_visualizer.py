"""Unit tests for HUD and computer vision visualizer annotations."""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

EDGE_ROOT = Path(__file__).resolve().parent.parent
if str(EDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(EDGE_ROOT))

from core.detector import DetectionResult
from core.visualizer import draw_driver_hud
from schemas.payload import DeviceStatus, LocationData


def test_draw_driver_hud_without_landmarks() -> None:
    """Verify HUD renders cleanly on a frame without face landmarks."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    status = DeviceStatus(
        device_id="pi4_01",
        driver_uid="driver_1",
        is_online=True,
        state="DRIVING",
        drowsy_confidence=0.15,
        yawn_confidence=0.05,
        location=LocationData(lat=-1.265, lng=116.831, speed_kmh=62.0),
        last_updated=1730000000,
    )

    annotated = draw_driver_hud(frame, status, detection=None)
    assert annotated is not None
    assert annotated.shape == (480, 640, 3)
    # HUD text and rectangles should have modified pixel values
    assert np.any(annotated > 0)


def test_draw_driver_hud_with_landmarks_and_critical_state() -> None:
    """Verify facial mesh contours and critical warning badge are drawn."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Generate 478 mock landmark points within image bounds
    mock_landmarks = [(200 + (i % 20) * 10, 150 + (i // 20) * 10) for i in range(478)]

    status = DeviceStatus(
        device_id="pi4_01",
        driver_uid="driver_1",
        is_online=True,
        state="CRITICAL_DROWSY",
        drowsy_confidence=0.92,
        yawn_confidence=0.85,
        location=LocationData(lat=None, lng=None, speed_kmh=75.0),
        last_updated=1730000000,
    )
    detection = DetectionResult(
        face_detected=True,
        drowsy_confidence=0.92,
        yawn_confidence=0.85,
        eye_blink_left=0.92,
        eye_blink_right=0.90,
        jaw_open=0.85,
        face_landmarks=mock_landmarks,
    )

    annotated = draw_driver_hud(frame, status, detection=detection)
    assert annotated.shape == (480, 640, 3)
    assert np.any(annotated > 0)

