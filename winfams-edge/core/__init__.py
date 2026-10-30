"""Core algorithms and processing modules for WinFams Edge."""

from core.camera_stream import CameraStream
from core.detector import (
    BaseDetector,
    DetectionResult,
    MediaPipeDetector,
    MockDetector,
    create_detector,
)
from core.state_machine import DriverState, FatigueStateMachine, StateOutput

__all__ = [
    "BaseDetector",
    "CameraStream",
    "DetectionResult",
    "DriverState",
    "FatigueStateMachine",
    "MediaPipeDetector",
    "MockDetector",
    "StateOutput",
    "create_detector",
]
