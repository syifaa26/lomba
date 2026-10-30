"""Unit tests for HW-03: Edge Main Orchestrator (main.py)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.detector import MockDetector
from core.state_machine import DriverState, FatigueStateMachine
from hardware.buzzer_controller import BuzzerController
from hardware.gps_reader import GPSReader
from main import EdgeOrchestrator
from schemas.payload import DeviceStatus, FatigueIncident


class MockCamera:
    """Mock camera stream yielding blank frames quickly without physical hardware."""

    def __init__(self) -> None:
        self.is_running: bool = False

    def start(self) -> MockCamera:
        self.is_running = True
        return self

    def read(self) -> tuple[bool, np.ndarray]:
        return True, np.zeros((480, 640, 3), dtype=np.uint8)

    def stop(self) -> None:
        self.is_running = False


def test_orchestrator_initialization_with_dependency_injection() -> None:
    """Test orchestrator binds all modular components cleanly."""
    detector = MockDetector(face_detected=True, drowsy_confidence=0.1, yawn_confidence=0.05)
    buzzer = BuzzerController(force_mock=True)
    gps = GPSReader(force_mock=True)
    camera = MockCamera()
    state_machine = FatigueStateMachine()

    orchestrator = EdgeOrchestrator(
        camera=camera,
        detector=detector,
        buzzer=buzzer,
        gps=gps,
        state_machine=state_machine,
        show_preview=False,
    )

    assert orchestrator.detector is detector
    assert orchestrator.buzzer is buzzer
    assert orchestrator.gps is gps
    assert orchestrator.state_machine is state_machine
    orchestrator.stop()


def test_orchestrator_step_normal_driving() -> None:
    """Test a single processing step under normal driving conditions."""
    detector = MockDetector(face_detected=True, drowsy_confidence=0.1, yawn_confidence=0.0)
    buzzer = BuzzerController(force_mock=True)
    gps = GPSReader(force_mock=True, mock_lat=-1.2653, mock_lng=116.8312, mock_speed_kmh=60.0)
    camera = MockCamera()
    state_machine = FatigueStateMachine()

    status_records: list[DeviceStatus] = []
    incident_records: list[FatigueIncident] = []

    orchestrator = EdgeOrchestrator(
        camera=camera,
        detector=detector,
        buzzer=buzzer,
        gps=gps,
        state_machine=state_machine,
        on_status=lambda s: status_records.append(s),
        on_incident=lambda i: incident_records.append(i),
    )

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    status, incident = orchestrator.step(frame=dummy_frame)

    assert status is not None
    assert status.state == DriverState.NORMAL.value
    assert status.drowsy_confidence == 0.1
    assert status.location.lat == -1.2653
    assert status.location.speed_kmh == 60.0
    assert incident is None
    assert len(incident_records) == 0
    assert len(status_records) == 1
    orchestrator.stop()


def test_orchestrator_step_critical_drowsy_trigger() -> None:
    """Test transition to CRITICAL_DROWSY triggers buzzer and emits FatigueIncident."""
    detector = MockDetector(face_detected=True, drowsy_confidence=0.85, yawn_confidence=0.0)
    buzzer = BuzzerController(force_mock=True)
    gps = GPSReader(force_mock=True, mock_lat=-1.2653, mock_lng=116.8312)
    camera = MockCamera()
    state_machine = FatigueStateMachine(drowsy_time_sec=1.0)

    incident_records: list[FatigueIncident] = []
    orchestrator = EdgeOrchestrator(
        camera=camera,
        detector=detector,
        buzzer=buzzer,
        gps=gps,
        state_machine=state_machine,
        on_incident=lambda inc: incident_records.append(inc),
    )

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Frame at t = 1000.0s (eyes closed starts)
    status, incident = orchestrator.step(frame=dummy_frame, current_time=1000.0)
    assert status is not None and status.state == DriverState.NORMAL.value
    assert incident is None

    # Frame at t = 1001.5s (eyes closed for 1.5s >= 1.0s threshold)
    status, incident = orchestrator.step(frame=dummy_frame, current_time=1001.5)

    assert status is not None
    assert status.state == DriverState.CRITICAL_DROWSY.value
    assert incident is not None
    assert incident.type == DriverState.CRITICAL_DROWSY.value
    assert incident.confidence_score == 0.85
    assert incident.location.lat == -1.2653
    assert len(incident_records) == 1
    assert buzzer.is_alerting is True

    orchestrator.stop()


def test_orchestrator_fault_tolerance_no_gps_lock() -> None:
    """Test orchestrator continues normal inference without crash when GPS has no lock."""
    detector = MockDetector(face_detected=True, drowsy_confidence=0.05, yawn_confidence=0.0)
    buzzer = BuzzerController(force_mock=True)
    gps = GPSReader(force_mock=True)
    camera = MockCamera()
    gps.set_mock_location(lat=None, lng=None, speed_kmh=0.0, heading=0.0, has_fix=False)

    orchestrator = EdgeOrchestrator(
        camera=camera,
        detector=detector,
        buzzer=buzzer,
        gps=gps,
    )

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    status, incident = orchestrator.step(frame=dummy_frame)

    assert status is not None
    assert status.location.lat is None
    assert status.location.lng is None
    assert status.state == DriverState.NORMAL.value
    assert incident is None
    orchestrator.stop()


def test_orchestrator_run_finite_frames() -> None:
    """Test orchestrator.run() executes finite iterations cleanly."""
    detector = MockDetector(face_detected=True, drowsy_confidence=0.0, yawn_confidence=0.0)
    buzzer = BuzzerController(force_mock=True)
    gps = GPSReader(force_mock=True)
    camera = MockCamera()

    orchestrator = EdgeOrchestrator(
        camera=camera,
        detector=detector,
        buzzer=buzzer,
        gps=gps,
    )

    orchestrator.run(max_frames=3)
    assert orchestrator._running is False
