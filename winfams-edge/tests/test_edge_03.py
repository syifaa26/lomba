"""Isolated unit tests for Task EDGE-03 (core/detector.py)."""

import os
import sys
from pathlib import Path

import numpy as np

# Add project root to sys.path
EDGE_ROOT = Path(__file__).resolve().parent.parent
if str(EDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(EDGE_ROOT))

# Ensure TF logging doesn't clutter output
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from config import settings
from core.detector import (
    BaseDetector,
    DetectionResult,
    MediaPipeDetector,
    MockDetector,
    create_detector,
    ensure_model_file,
)


def test_mock_detector() -> None:
    """Test MockDetector behavior and DetectionResult format."""
    detector = MockDetector(face_detected=True, drowsy_confidence=0.75, yawn_confidence=0.82)
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    result = detector.process_frame(dummy_frame)
    assert isinstance(result, DetectionResult)
    assert result.face_detected is True
    assert result.drowsy_confidence == 0.75
    assert result.yawn_confidence == 0.82

    detector.set_scores(face_detected=False, drowsy_confidence=0.0, yawn_confidence=0.0)
    result2 = detector.process_frame(dummy_frame)
    assert result2.face_detected is False
    detector.close()


def test_detector_factory() -> None:
    """Test create_detector factory function."""
    mock_det = create_detector(model_type="mock")
    assert isinstance(mock_det, MockDetector)

    try:
        create_detector(model_type="invalid_model_type")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_ensure_model_file() -> None:
    """Test that model file exists and is valid."""
    model_path = ensure_model_file(settings.MEDIAPIPE_MODEL_PATH)
    assert model_path.exists()
    assert model_path.stat().st_size > 1_000_000


def test_mediapipe_detector_inference() -> None:
    """Test MediaPipeDetector inference on synthetic test frame."""
    detector = create_detector(model_type="mediapipe", model_path=settings.MEDIAPIPE_MODEL_PATH)
    assert isinstance(detector, MediaPipeDetector)

    # Empty / black frame
    black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = detector.process_frame(black_frame)

    assert isinstance(result, DetectionResult)
    # On solid black frame, no face should be detected
    assert result.face_detected is False
    assert result.drowsy_confidence == 0.0
    assert result.yawn_confidence == 0.0

    # None frame handling
    none_result = detector.process_frame(None)  # type: ignore
    assert none_result.face_detected is False

    detector.close()


if __name__ == "__main__":
    test_mock_detector()
    test_detector_factory()
    test_ensure_model_file()
    test_mediapipe_detector_inference()
    print("ALL DETECTOR TESTS PASSED SUCCESSFULLY!")

