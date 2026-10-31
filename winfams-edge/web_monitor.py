"""Convenience launcher for WinFams Edge with live web dashboard enabled."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
from typing import Any

from config.settings import setup_logging
from hardware.buzzer_controller import BuzzerController
from hardware.gps_reader import GPSReader
from main import EdgeOrchestrator
from services.api_client import BackgroundSyncWorker
from services.web_streamer import WebStreamer

logger = logging.getLogger("winfams.web_monitor")


def main() -> None:
    """Launch WinFams Edge with browser-accessible live cockpit."""
    setup_logging()
    parser = argparse.ArgumentParser(description="WinFams Edge Live Web Monitor")
    parser.add_argument("--port", type=int, default=5000, help="Web port (default 5000)")
    parser.add_argument("--mock", action="store_true", help="Run with mock hardware")
    parser.add_argument("--no-sync", action="store_true", help="Disable API sync")
    args = parser.parse_args()

    detector = None
    buzzer = None
    gps = None
    sync_worker = None

    if args.mock:
        from core.detector import MockDetector
        detector = MockDetector()
        buzzer = BuzzerController(force_mock=True)
        gps = GPSReader(force_mock=True)

    if not args.no_sync:
        sync_worker = BackgroundSyncWorker()

    web_streamer = WebStreamer(port=args.port)
    orchestrator = EdgeOrchestrator(
        detector=detector,
        buzzer=buzzer,
        gps=gps,
        sync_worker=sync_worker,
        web_streamer=web_streamer,
    )

    signal.signal(signal.SIGINT, lambda s, f: (orchestrator.stop(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (orchestrator.stop(), sys.exit(0)))

    logger.info("==========================================================")
    logger.info("🚀 WinFams Live Web Cockpit Aktif!")
    logger.info("👉 Buka di browser laptop/HP: http://<IP_RASPBERRY_PI>:%d", args.port)
    logger.info("==========================================================")

    orchestrator.run()


if __name__ == "__main__":
    main()

