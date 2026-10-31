"""Pre-trained computer vision detector wrapper for drowsiness and yawn analysis.

Uses MediaPipe Face Landmarker with blendshapes (eyeBlinkLeft, eyeBlinkRight, jawOpen).
Provides clean BaseDetector interface to allow plug-and-play model swapping.
"""

from __future__ import annotations

import logging
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Standardized output of driver face detection and fatigue indicators."""

    face_detected: bool
    drowsy_confidence: float
    yawn_confidence: float
    eye_blink_left: float = 0.0
    eye_blink_right: float = 0.0
    jaw_open: float = 0.0
    face_landmarks: list[tuple[int, int]] | None = None


class BaseDetector(ABC):
    """Abstract base detector interface for driver fatigue analysis."""

    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> DetectionResult:
        """Process a BGR video frame and return drowsiness & yawn confidences."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Release detector resources."""
        raise NotImplementedError


def ensure_model_file(
    model_path: Path,
    download_url: str = (
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
        "face_landmarker/float16/1/face_landmarker.task"
    ),
) -> Path:
    """Download pre-trained MediaPipe model if not already present."""
    model_path = Path(model_path)
    if not model_path.exists():
        logger.info("Model file not found at %s. Downloading from %s...", model_path, download_url)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(download_url, str(model_path))
        logger.info("Model downloaded successfully. File size: %d bytes", model_path.stat().st_size)
    return model_path


class MediaPipeDetector(BaseDetector):
    """MediaPipe Face Landmarker implementation extracting eye and jaw blendshapes."""

    def __init__(self, model_path: Path | str) -> None:
        """Initialize MediaPipe Face Landmarker with blendshapes enabled."""
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import (
            FaceLandmarker,
            FaceLandmarkerOptions,
            RunningMode,
        )

        self._mp = mp
        self.model_path: Path = ensure_model_file(Path(model_path))

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(self.model_path)),
            output_face_blendshapes=True,
            num_faces=1,
            running_mode=RunningMode.IMAGE,
        )
        self._landmarker: FaceLandmarker = FaceLandmarker.create_from_options(options)
        logger.info("MediaPipeDetector initialized with model: %s", self.model_path)

    def process_frame(self, frame: np.ndarray) -> DetectionResult:
        """Detect face landmarks and extract blink and yawn blendshape scores."""
        if frame is None or frame.size == 0:
            return DetectionResult(face_detected=False, drowsy_confidence=0.0, yawn_confidence=0.0)

        # Convert BGR to RGB contiguous array for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(
            image_format=self._mp.ImageFormat.SRGB,
            data=rgb_frame,
        )

        result = self._landmarker.detect(mp_image)

        if not result.face_blendshapes or len(result.face_blendshapes) == 0:
            return DetectionResult(face_detected=False, drowsy_confidence=0.0, yawn_confidence=0.0)

        eye_blink_left: float = 0.0
        eye_blink_right: float = 0.0
        jaw_open: float = 0.0

        for category in result.face_blendshapes[0]:
            name = category.category_name
            if name == "eyeBlinkLeft":
                eye_blink_left = float(category.score)
            elif name == "eyeBlinkRight":
                eye_blink_right = float(category.score)
            elif name == "jawOpen":
                jaw_open = float(category.score)

        drowsy_confidence = max(eye_blink_left, eye_blink_right)
        yawn_confidence = jaw_open

        landmarks: list[tuple[int, int]] | None = None
        if result.face_landmarks and len(result.face_landmarks) > 0:
            h, w = frame.shape[:2]
            landmarks = [
                (int(pt.x * w), int(pt.y * h)) for pt in result.face_landmarks[0]
            ]

        return DetectionResult(
            face_detected=True,
            drowsy_confidence=round(drowsy_confidence, 4),
            yawn_confidence=round(yawn_confidence, 4),
            eye_blink_left=round(eye_blink_left, 4),
            eye_blink_right=round(eye_blink_right, 4),
            jaw_open=round(jaw_open, 4),
            face_landmarks=landmarks,
        )

    def close(self) -> None:
        """Release FaceLandmarker native resources."""
        if hasattr(self, "_landmarker") and self._landmarker is not None:
            self._landmarker.close()
            logger.info("MediaPipeDetector closed.")


class MockDetector(BaseDetector):
    """Mock detector for deterministic testing without camera or model weight loading."""

    def __init__(
        self,
        face_detected: bool = True,
        drowsy_confidence: float = 0.0,
        yawn_confidence: float = 0.0,
    ) -> None:
        self.face_detected: bool = face_detected
        self.drowsy_confidence: float = drowsy_confidence
        self.yawn_confidence: float = yawn_confidence

    def set_scores(
        self,
        face_detected: bool,
        drowsy_confidence: float,
        yawn_confidence: float,
    ) -> None:
        """Update mock return values."""
        self.face_detected = face_detected
        self.drowsy_confidence = drowsy_confidence
        self.yawn_confidence = yawn_confidence

    def process_frame(self, frame: np.ndarray) -> DetectionResult:
        """Return configured mock detection result."""
        return DetectionResult(
            face_detected=self.face_detected,
            drowsy_confidence=self.drowsy_confidence,
            yawn_confidence=self.yawn_confidence,
            eye_blink_left=self.drowsy_confidence,
            eye_blink_right=self.drowsy_confidence,
            jaw_open=self.yawn_confidence,
        )

    def close(self) -> None:
        """No-op cleanup for mock detector."""
        pass


def create_detector(
    model_type: str = "mediapipe",
    model_path: Path | str | None = None,
) -> BaseDetector:
    """Factory creating appropriate detector based on type."""
    if model_type == "mock":
        return MockDetector()
    if model_type == "mediapipe":
        if model_path is None:
            from config import settings
            model_path = settings.MEDIAPIPE_MODEL_PATH
        return MediaPipeDetector(model_path=model_path)
    raise ValueError(f"Unsupported detector model_type: {model_type}")

