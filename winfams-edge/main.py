"""Edge main orchestrator for WinFams in-cabin driver safety system."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from typing import Any, Callable

import cv2
import numpy as np

from config import settings
from config.settings import setup_logging
from core.camera_stream import CameraStream
from core.detector import BaseDetector, create_detector
from core.state_machine import DriverState, FatigueStateMachine
from hardware.buzzer_controller import BuzzerController
from hardware.gps_reader import GPSReader
from schemas.payload import DeviceStatus, FatigueIncident, HeartbeatPayload
from services.api_client import BackgroundSyncWorker
from services.cloud_sync import CloudSyncService
from services.web_streamer import WebStreamer

logger = logging.getLogger("winfams.orchestrator")


class EdgeOrchestrator:
    """Coordinates edge hardware, AI detection, buzzer, GPS, and sync worker."""

    def __init__(
        self,
        camera: Any | None = None,
        detector: BaseDetector | None = None,
        state_machine: FatigueStateMachine | None = None,
        buzzer: BuzzerController | None = None,
        gps: GPSReader | None = None,
        cloud_sync: CloudSyncService | None = None,
        sync_worker: BackgroundSyncWorker | None = None,
        web_streamer: WebStreamer | None = None,
        on_status: Callable[[DeviceStatus], None] | None = None,
        on_incident: Callable[[FatigueIncident], None] | None = None,
        show_preview: bool = False,
    ) -> None:
        self.camera: Any = camera or CameraStream(
            src=settings.CAMERA_INDEX,
            width=settings.CAMERA_WIDTH,
            height=settings.CAMERA_HEIGHT,
            fps=settings.CAMERA_FPS,
        )
        self.detector: BaseDetector = detector or create_detector(model_type=settings.MODEL_TYPE)
        self.state_machine: FatigueStateMachine = state_machine or FatigueStateMachine()
        self.buzzer: BuzzerController = buzzer or BuzzerController()
        self.gps: GPSReader = gps or GPSReader()
        self.cloud_sync: CloudSyncService | None = cloud_sync
        self.sync_worker: BackgroundSyncWorker | None = sync_worker
        self.web_streamer: WebStreamer | None = web_streamer
        self.on_status: Callable[[DeviceStatus], None] | None = on_status
        self.on_incident: Callable[[FatigueIncident], None] | None = on_incident
        self.show_preview: bool = show_preview

        self._running: bool = False
        self._incident_seq: int = 0

    def start(self) -> None:
        """Start hardware acquisition and sync worker threads."""
        self._running = True
        logger.info("Starting Edge subsystems...")
        self.gps.start()
        self.camera.start()
        if self.cloud_sync is not None:
            self.cloud_sync.start()
        if self.sync_worker is not None:
            self.sync_worker.start()
        if self.web_streamer is not None:
            self.web_streamer.start()
        logger.info("WinFams Edge Orchestrator is running.")

    def stop(self) -> None:
        """Stop background threads and release resources."""
        if not self._running:
            return
        logger.info("Stopping WinFams Edge Orchestrator...")
        self._running = False
        for res in (self.camera, self.gps, self.buzzer, self.detector):
            if hasattr(res, "stop"):
                res.stop()
            if hasattr(res, "close"):
                res.close()
        if self.cloud_sync is not None:
            self.cloud_sync.stop()
        if self.sync_worker is not None:
            self.sync_worker.stop()
        if self.web_streamer is not None:
            self.web_streamer.stop()
        if self.show_preview:
            cv2.destroyAllWindows()
        logger.info("All Edge subsystems stopped.")

    def step(
        self,
        frame: np.ndarray | None = None,
        current_time: float | None = None,
    ) -> tuple[DeviceStatus | None, FatigueIncident | None]:
        """Process a single video frame and evaluate driver state."""
        if frame is None:
            grabbed, frame = self.camera.read()
            if not grabbed or frame is None:
                return None, None

        # 1. Vision Inference & State Machine
        detection = self.detector.process_frame(frame)
        state_output = self.state_machine.update(detection, current_time=current_time)
        location = self.gps.get_location()

        # 2. Audible Alert and Incident Trigger
        incident: FatigueIncident | None = None
        now_ts = int(current_time) if current_time is not None else int(time.time())

        if state_output.incident_triggered:
            self._incident_seq += 1
            if state_output.incident_type == DriverState.CRITICAL_DROWSY.value:
                self.buzzer.trigger_critical()
            elif state_output.incident_type == DriverState.WARNING_FATIGUE.value:
                self.buzzer.trigger_warning()

            incident = FatigueIncident(
                incident_id=f"inc_{now_ts}_{self._incident_seq}",
                device_id=settings.DEVICE_ID,
                driver_uid=settings.DRIVER_UID,
                family_group_id=settings.FAMILY_GROUP_ID,
                type=state_output.incident_type or state_output.state.value,
                confidence_score=state_output.confidence_score,
                duration_seconds=state_output.duration_seconds,
                location=location,
                timestamp=now_ts,
            )
            logger.warning("FATIGUE INCIDENT EMITTED: %s", incident.type)
            if self.on_incident is not None:
                self.on_incident(incident)
            if self.cloud_sync is not None:
                self.cloud_sync.report_incident(incident)
            if self.sync_worker is not None:
                self.sync_worker.enqueue_incident(incident)
        elif state_output.state == DriverState.CRITICAL_DROWSY and not self.buzzer.is_alerting:
            self.buzzer.trigger_critical()

        # 3. Status Snapshot & Telemetry
        status = DeviceStatus(
            device_id=settings.DEVICE_ID,
            driver_uid=settings.DRIVER_UID,
            is_online=True,
            state=state_output.state.value,
            drowsy_confidence=detection.drowsy_confidence,
            yawn_confidence=detection.yawn_confidence,
            location=location,
            last_updated=now_ts,
        )
        if self.on_status is not None:
            self.on_status(status)
        if self.cloud_sync is not None:
            self.cloud_sync.update_status(status)
        if self.sync_worker is not None:
            hb = HeartbeatPayload(
                device_uid=settings.DEVICE_UID,
                state=status.state,
                drowsy_confidence=status.drowsy_confidence,
                yawn_confidence=status.yawn_confidence,
                location=location,
                timestamp=now_ts,
            )
            self.sync_worker.update_telemetry(hb)

        if self.show_preview:
            self._render_preview(frame, status, detection)
        if self.web_streamer is not None:
            self.web_streamer.update(
                frame,
                status,
                buzzer_active=getattr(self.buzzer, "is_alerting", False),
                detection=detection,
            )

        return status, incident

    def _render_preview(self, frame: np.ndarray, status: DeviceStatus, detection: Any = None) -> None:
        from core.visualizer import draw_driver_hud
        annotated = draw_driver_hud(frame.copy(), status, detection)
        cv2.imshow("WinFams Edge Monitor", annotated)
        cv2.waitKey(1)

    def run(self, max_frames: int | None = None) -> None:
        """Execute non-blocking loop continuously monitoring driver state."""
        self.start()
        processed_count = 0
        try:
            while self._running:
                status, _ = self.step()
                if status is not None:
                    processed_count += 1
                    if max_frames is not None and processed_count >= max_frames:
                        break
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received.")
        finally:
            self.stop()


def main() -> None:
    """CLI entrypoint for executing Edge monitor."""
    setup_logging()
    parser = argparse.ArgumentParser(description="WinFams Edge Driver Monitor")
    parser.add_argument("--preview", action="store_true", help="Display desktop preview")
    parser.add_argument("--web", action="store_true", help="Launch live web dashboard")
    parser.add_argument("--port", type=int, default=5000, help="Web port (default 5000)")
    parser.add_argument("--mock", action="store_true", help="Run mock hardware")
    parser.add_argument("--frames", type=int, default=None, help="Stop after N frames")
    parser.add_argument("--no-sync", action="store_true", help="Disable API sync worker")
    args = parser.parse_args()

    detector = None
    buzzer, gps, sync_worker = None, None, None
    if args.mock:
        from core.detector import MockDetector
        detector, buzzer = MockDetector(), BuzzerController(force_mock=True)
        gps = GPSReader(force_mock=True)

    if not args.no_sync:
        sync_worker = BackgroundSyncWorker()

    web_streamer = WebStreamer(port=args.port) if args.web else None

    orchestrator = EdgeOrchestrator(
        detector=detector,
        buzzer=buzzer,
        gps=gps,
        sync_worker=sync_worker,
        web_streamer=web_streamer,
        show_preview=args.preview,
    )

    signal.signal(signal.SIGINT, lambda s, f: (orchestrator.stop(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (orchestrator.stop(), sys.exit(0)))
    orchestrator.run(max_frames=args.frames)


if __name__ == "__main__":
    main()
