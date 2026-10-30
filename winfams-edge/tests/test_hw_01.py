"""Isolated unit tests for Task HW-01 (hardware/buzzer_controller.py)."""

import sys
import time
from pathlib import Path

# Add project root to sys.path
EDGE_ROOT = Path(__file__).resolve().parent.parent
if str(EDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(EDGE_ROOT))

from hardware.buzzer_controller import BuzzerController, MockBuzzerHardware


def test_mock_buzzer_hardware() -> None:
    """Verify MockBuzzerHardware toggle behavior."""
    mock_hw = MockBuzzerHardware(pin=17)
    assert not mock_hw.is_active
    mock_hw.on()
    assert mock_hw.is_active
    assert mock_hw.toggle_count == 1
    mock_hw.off()
    assert not mock_hw.is_active
    mock_hw.close()


def test_buzzer_controller_fallback_and_non_blocking() -> None:
    """Verify BuzzerController falls back to mock and triggers non-blocking."""
    controller = BuzzerController(pin=17)
    # On Windows / PC environment, it should automatically detect absence of GPIO pins
    assert controller.is_mock is True

    start_time = time.perf_counter()
    # Trigger critical pattern (4 * (0.04 + 0.04) = 0.32 seconds nominal)
    controller.trigger_critical(count=4, on_sec=0.04, off_sec=0.04)
    elapsed = time.perf_counter() - start_time

    # Must return immediately (< 20ms), proving it is 100% non-blocking!
    assert elapsed < 0.05, f"trigger_critical blocked the caller for {elapsed:.4f}s!"
    assert controller.is_alerting is True

    # Wait for pattern to complete
    deadline = time.time() + 1.5
    while controller.is_alerting and time.time() < deadline:
        time.sleep(0.05)

    assert controller.is_alerting is False
    controller.close()


def test_buzzer_immediate_stop() -> None:
    """Verify stop() cancels an active alert immediately."""
    controller = BuzzerController(pin=17, force_mock=True)

    # Launch long alert pattern (10 * 0.2s = 2 seconds)
    controller.trigger_critical(count=10, on_sec=0.1, off_sec=0.1)
    assert controller.is_alerting is True

    time.sleep(0.08)
    controller.stop()

    assert controller.is_alerting is False
    assert controller._buzzer.is_active is False
    controller.close()


def test_buzzer_context_manager() -> None:
    """Verify context manager protocol closes resources cleanly."""
    with BuzzerController(pin=17, force_mock=True) as controller:
        controller.trigger_warning(count=2, on_sec=0.05, off_sec=0.05)
        assert controller.is_alerting is True

    # Exited context
    assert not controller.is_alerting


if __name__ == "__main__":
    test_mock_buzzer_hardware()
    test_buzzer_controller_fallback_and_non_blocking()
    test_buzzer_immediate_stop()
    test_buzzer_context_manager()
    print("ALL BUZZER CONTROLLER TESTS PASSED SUCCESSFULLY!")
