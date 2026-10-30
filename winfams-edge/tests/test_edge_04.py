"""Isolated unit tests for Task EDGE-04 (core/state_machine.py)."""

import sys
from pathlib import Path

# Add project root to sys.path
EDGE_ROOT = Path(__file__).resolve().parent.parent
if str(EDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(EDGE_ROOT))

from core.detector import DetectionResult
from core.state_machine import DriverState, FatigueStateMachine


def test_normal_state() -> None:
    """Verify normal alert state when eyes are open."""
    sm = FatigueStateMachine()
    detection = DetectionResult(face_detected=True, drowsy_confidence=0.1, yawn_confidence=0.05)
    out = sm.update(detection, current_time=1000.0)

    assert out.state == DriverState.NORMAL
    assert not out.incident_triggered
    assert out.consecutive_drowsy_sec == 0.0


def test_critical_drowsy_trigger() -> None:
    """Verify transition to CRITICAL_DROWSY when eyes closed >= 1.5 seconds."""
    sm = FatigueStateMachine(drowsy_time_sec=1.5, blink_threshold=0.55)
    closed = DetectionResult(face_detected=True, drowsy_confidence=0.85, yawn_confidence=0.0)

    # T=0.0s: eyes closed starts
    out1 = sm.update(closed, current_time=10.0)
    assert out1.state == DriverState.NORMAL
    assert not out1.incident_triggered

    # T=1.0s: eyes still closed (1.0s < 1.5s)
    out2 = sm.update(closed, current_time=11.0)
    assert out2.state == DriverState.NORMAL
    assert not out2.incident_triggered

    # T=1.5s: eyes closed for 1.5s -> Trigger CRITICAL_DROWSY
    out3 = sm.update(closed, current_time=11.5)
    assert out3.state == DriverState.CRITICAL_DROWSY
    assert out3.incident_triggered is True
    assert out3.incident_type == "CRITICAL_DROWSY"
    assert out3.duration_seconds == 1.5

    # T=2.0s: eyes still closed -> no duplicate incident spam
    out4 = sm.update(closed, current_time=12.0)
    assert out4.state == DriverState.CRITICAL_DROWSY
    assert out4.incident_triggered is False

    # Eyes open again -> return to NORMAL
    open_eyes = DetectionResult(face_detected=True, drowsy_confidence=0.1, yawn_confidence=0.0)
    out5 = sm.update(open_eyes, current_time=12.1)
    assert out5.state == DriverState.NORMAL
    assert out5.consecutive_drowsy_sec == 0.0


def test_warning_fatigue_yawn_trigger() -> None:
    """Verify WARNING_FATIGUE triggered on 3 yawns >= 2.5s within 10 minutes."""
    sm = FatigueStateMachine(
        yawn_threshold=0.60,
        yawn_time_sec=2.5,
        yawn_count_trigger=3,
        yawn_window_sec=600.0,
    )
    yawning = DetectionResult(face_detected=True, drowsy_confidence=0.1, yawn_confidence=0.75)
    normal = DetectionResult(face_detected=True, drowsy_confidence=0.1, yawn_confidence=0.1)

    t = 100.0

    # Yawn 1: duration 2.5s
    sm.update(yawning, current_time=t)
    out_y1 = sm.update(yawning, current_time=t + 2.5)
    assert out_y1.yawn_count_in_window == 1
    assert out_y1.state == DriverState.NORMAL
    sm.update(normal, current_time=t + 3.0)

    # Yawn 2: 1 minute later, duration 3.0s
    t = 160.0
    sm.update(yawning, current_time=t)
    out_y2 = sm.update(yawning, current_time=t + 3.0)
    assert out_y2.yawn_count_in_window == 2
    assert out_y2.state == DriverState.NORMAL
    sm.update(normal, current_time=t + 3.5)

    # Yawn 3: 2 minutes later, duration 2.5s -> Triggers WARNING_FATIGUE
    t = 280.0
    sm.update(yawning, current_time=t)
    out_y3 = sm.update(yawning, current_time=t + 2.5)
    assert out_y3.yawn_count_in_window == 3
    assert out_y3.state == DriverState.WARNING_FATIGUE
    assert out_y3.incident_triggered is True
    assert out_y3.incident_type == "WARNING_FATIGUE"


def test_yawn_window_pruning() -> None:
    """Verify yawns outside 10 minute (600s) window are pruned."""
    sm = FatigueStateMachine(
        yawn_threshold=0.60,
        yawn_time_sec=2.5,
        yawn_count_trigger=3,
        yawn_window_sec=600.0,
    )
    yawning = DetectionResult(face_detected=True, drowsy_confidence=0.1, yawn_confidence=0.8)
    normal = DetectionResult(face_detected=True, drowsy_confidence=0.1, yawn_confidence=0.1)

    # Yawn 1 at T=100s
    sm.update(yawning, current_time=100.0)
    sm.update(yawning, current_time=102.5)
    sm.update(normal, current_time=103.0)
    assert len(sm._yawn_history) == 1

    # Jump to T=750s (> 600s after Yawn 1)
    out = sm.update(normal, current_time=750.0)
    assert out.yawn_count_in_window == 0
    assert len(sm._yawn_history) == 0


def test_critical_drowsy_overrides_warning_fatigue() -> None:
    """Verify that CRITICAL_DROWSY takes priority over WARNING_FATIGUE."""
    sm = FatigueStateMachine(
        drowsy_time_sec=1.5,
        yawn_count_trigger=1,
        yawn_time_sec=1.0,
    )
    yawn = DetectionResult(face_detected=True, drowsy_confidence=0.1, yawn_confidence=0.9)
    sm.update(yawn, current_time=10.0)
    out_warn = sm.update(yawn, current_time=11.0)
    assert out_warn.state == DriverState.WARNING_FATIGUE

    # Both yawning and eyes closed >= 1.5s -> must be CRITICAL_DROWSY
    both = DetectionResult(face_detected=True, drowsy_confidence=0.9, yawn_confidence=0.9)
    sm.update(both, current_time=12.0)
    out_crit = sm.update(both, current_time=13.5)
    assert out_crit.state == DriverState.CRITICAL_DROWSY


if __name__ == "__main__":
    test_normal_state()
    test_critical_drowsy_trigger()
    test_warning_fatigue_yawn_trigger()
    test_yawn_window_pruning()
    test_critical_drowsy_overrides_warning_fatigue()
    print("ALL STATE MACHINE TESTS PASSED SUCCESSFULLY!")

