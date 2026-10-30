"""Application configuration and constants for WinFams Edge.

Provides threshold constants, hardware pinout mappings, model parameters,
FastAPI endpoints, and unified logging configuration.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

# Base paths
BASE_DIR: Path = Path(__file__).resolve().parent.parent
MODELS_DIR: Path = BASE_DIR / "models_weights"
DATA_DIR: Path = BASE_DIR / "data"

# Ensure runtime directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Hardware Mock Mode Switch
MOCK_HARDWARE: bool = os.getenv("WINFAMS_MOCK_HARDWARE", "false").lower() in (
    "true",
    "1",
    "yes",
)

# Edge Device Identity
DEVICE_UID: str = os.getenv(
    "WINFAMS_DEVICE_UID", os.getenv("WINFAMS_DEVICE_ID", "pi4_car_01")
)
DEVICE_ID: str = DEVICE_UID  # Backward-compatible alias
DRIVER_UID: str = os.getenv("WINFAMS_DRIVER_UID", "user_123")
FAMILY_GROUP_ID: str = os.getenv("WINFAMS_FAMILY_GROUP_ID", "fam_001")

# FastAPI Backend & IoT Edge Ingestion Configuration
API_BASE_URL: str = os.getenv("WINFAMS_API_BASE_URL", "http://localhost:8000")
DEVICE_API_KEY: str = os.getenv("WINFAMS_DEVICE_API_KEY", "dev_api_key_secret_123")
HEARTBEAT_ENDPOINT: str = f"{API_BASE_URL}/api/v1/edge/heartbeat"
INCIDENTS_ENDPOINT: str = f"{API_BASE_URL}/api/v1/edge/incidents"

# Computer Vision & Fatigue Detection Thresholds
BLINK_THRESHOLD: float = float(os.getenv("WINFAMS_BLINK_THRESHOLD", "0.55"))
YAWN_THRESHOLD: float = float(os.getenv("WINFAMS_YAWN_THRESHOLD", "0.60"))
DROWSY_TIME_SEC: float = float(os.getenv("WINFAMS_DROWSY_TIME_SEC", "1.5"))
YAWN_TIME_SEC: float = float(os.getenv("WINFAMS_YAWN_TIME_SEC", "2.5"))
YAWN_COUNT_TRIGGER: int = int(os.getenv("WINFAMS_YAWN_COUNT_TRIGGER", "3"))
YAWN_WINDOW_SEC: float = float(os.getenv("WINFAMS_YAWN_WINDOW_SEC", "600.0"))

# Camera Configuration
CAMERA_INDEX: int = int(os.getenv("WINFAMS_CAMERA_INDEX", "0"))
CAMERA_WIDTH: int = int(os.getenv("WINFAMS_CAMERA_WIDTH", "640"))
CAMERA_HEIGHT: int = int(os.getenv("WINFAMS_CAMERA_HEIGHT", "480"))
CAMERA_FPS: int = int(os.getenv("WINFAMS_CAMERA_FPS", "30"))

# Pre-trained Model Configuration
MODEL_TYPE: str = os.getenv("WINFAMS_MODEL_TYPE", "mediapipe")
MEDIAPIPE_MODEL_PATH: Path = MODELS_DIR / "face_landmarker.task"
MEDIAPIPE_MODEL_URL: str = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)

# Hardware: Buzzer Configuration (Raspberry Pi GPIO Pin BCM)
BUZZER_PIN: int = int(os.getenv("WINFAMS_BUZZER_PIN", "17"))
BUZZER_CRITICAL_BEEP_DURATION: float = 0.15
BUZZER_WARNING_BEEP_DURATION: float = 0.40

# Hardware: GPS Serial Configuration
GPS_SERIAL_PORT: str = os.getenv("WINFAMS_GPS_PORT", "/dev/serial0")
GPS_BAUDRATE: int = int(os.getenv("WINFAMS_GPS_BAUDRATE", "9600"))
GPS_TIMEOUT: float = float(os.getenv("WINFAMS_GPS_TIMEOUT", "1.0"))

# Telemetry, Offline Buffer & Sync Settings
TELEMETRY_INTERVAL_SEC: float = float(
    os.getenv("WINFAMS_TELEMETRY_INTERVAL_SEC", "10.0")
)
SPEED_THRESHOLD_KMH: float = float(os.getenv("WINFAMS_SPEED_THRESHOLD_KMH", "5.0"))
SQLITE_DB_PATH: Path = DATA_DIR / "offline_queue.db"
FIREBASE_CREDENTIALS_PATH: Path = (
    BASE_DIR / os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_credentials.json")
)
FIREBASE_RTDB_URL: str = os.getenv(
    "FIREBASE_RTDB_URL", "https://winfams-default-rtdb.firebaseio.com"
)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return root logger with standard timestamp and format."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        force=True,
    )
    return logging.getLogger("winfams")
