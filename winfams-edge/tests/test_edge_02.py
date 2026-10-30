"""Isolated unit tests for Task EDGE-02 (core/camera_stream.py)."""

import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np

# Add project root to sys.path
EDGE_ROOT = Path(__file__).resolve().parent.parent
if str(EDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(EDGE_ROOT))

from core.camera_stream import CameraStream


def create_dummy_video(file_path: str, count: int = 20) -> None:
    """Create a temporary avi video file for isolated testing without physical webcam."""
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    out = cv2.VideoWriter(file_path, fourcc, 30.0, (320, 240))
    for i in range(count):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.putText(
            frame,
            f"Frame {i}",
            (30, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
        )
        out.write(frame)
    out.release()


def test_camera_stream_with_video_file() -> None:
    """Test CameraStream thread reading from an actual video file source."""
    with tempfile.NamedTemporaryFile(suffix=".avi", delete=False) as tmp_file:
        video_path = tmp_file.name

    try:
        create_dummy_video(video_path, count=25)

        stream = CameraStream(src=video_path, width=320, height=240, fps=30)
        assert not stream.is_running

        stream.start()
        assert stream.is_running

        # Allow worker thread to read frames
        time.sleep(0.15)

        grabbed, frame = stream.read()
        assert grabbed is True
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (240, 320, 3)

        stream.stop()
        assert not stream.is_running

        grabbed_after, frame_after = stream.read()
        assert grabbed_after is False
        assert frame_after is None
    finally:
        time.sleep(0.05)
        if Path(video_path).exists():
            Path(video_path).unlink()


def test_camera_stream_context_manager() -> None:
    """Test CameraStream context manager protocol."""
    with tempfile.NamedTemporaryFile(suffix=".avi", delete=False) as tmp_file:
        video_path = tmp_file.name

    try:
        create_dummy_video(video_path, count=15)

        with CameraStream(src=video_path, width=320, height=240) as stream:
            assert stream.is_running
            time.sleep(0.1)
            grabbed, frame = stream.read()
            assert grabbed is True
            assert frame is not None

        # Exited context
        assert not stream.is_running
    finally:
        time.sleep(0.05)
        if Path(video_path).exists():
            Path(video_path).unlink()


def test_camera_stream_unavailable_source() -> None:
    """Test CameraStream handles unavailable source gracefully without crashing."""
    stream = CameraStream(
        src="nonexistent_invalid_camera_path.avi",
        reconnect_interval_sec=0.1,
    )
    stream.start()
    assert stream.is_running

    # Give thread a moment to try reading
    time.sleep(0.15)

    grabbed, frame = stream.read()
    assert grabbed is False
    assert frame is None

    stream.stop()
    assert not stream.is_running


if __name__ == "__main__":
    test_camera_stream_with_video_file()
    test_camera_stream_context_manager()
    test_camera_stream_unavailable_source()
    print("ALL CAMERA STREAM TESTS PASSED SUCCESSFULLY!")
