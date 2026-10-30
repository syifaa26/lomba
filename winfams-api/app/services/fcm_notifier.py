"""Firebase Cloud Messaging (FCM) emergency alert service."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.family import FamilyMember
from app.models.user import User

logger = logging.getLogger("winfams-api.fcm")


class FCMNotifierService:
    """Service handling high-priority push notifications via Firebase Admin SDK."""

    def __init__(self) -> None:
        self.is_mock_mode: bool = True
        self._initialize_firebase()

    def _initialize_firebase(self) -> None:
        """Initialize Firebase App with credentials or fallback to mock mode."""
        if firebase_admin._apps:
            self.is_mock_mode = False
            return

        cred_path = Path(settings.FIREBASE_CREDENTIALS_PATH)
        if cred_path.is_file():
            try:
                cred = credentials.Certificate(str(cred_path))
                firebase_admin.initialize_app(cred)
                self.is_mock_mode = False
                logger.info("Firebase Admin SDK successfully initialized.")
                return
            except Exception as e:
                logger.warning("Failed to initialize Firebase with credentials: %s", e)

        self.is_mock_mode = True
        logger.info(
            "Firebase credentials not found (%s). FCM service running in MOCK mode.",
            settings.FIREBASE_CREDENTIALS_PATH,
        )

    def send_notification_to_tokens(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> int:
        """Send high-priority notification to a list of device registration tokens."""
        valid_tokens = [t.strip() for t in tokens if t and t.strip()]
        if not valid_tokens:
            return 0

        clean_data = {k: str(v) for k, v in (data or {}).items()}

        if self.is_mock_mode:
            logger.info(
                "[MOCK FCM] Sent push to %d devices: '%s' | Body: '%s'",
                len(valid_tokens),
                title,
                body,
            )
            return len(valid_tokens)

        # Production Firebase delivery
        try:
            message = messaging.MulticastMessage(
                tokens=valid_tokens,
                notification=messaging.Notification(title=title, body=body),
                data=clean_data,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default",
                        channel_id="winfams_emergency_channel",
                    ),
                ),
                apns=messaging.APNSConfig(
                    headers={"apns-priority": "10"},
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound="default", badge=1)
                    ),
                ),
            )
            response = messaging.send_each_for_multicast(message)
            logger.info(
                "FCM Batch delivery: %d succeeded, %d failed",
                response.success_count,
                response.failure_count,
            )
            return response.success_count
        except Exception as e:
            logger.error("Error dispatching FCM multicast message: %s", e)
            return 0

    def send_emergency_fatigue_alert(
        self,
        db: Session,
        family_id: int,
        driver_name: str,
        vehicle_name: str,
        incident_type: str,
        speed_kmh: float,
        lat: float | None = None,
        lng: float | None = None,
    ) -> int:
        """Dispatch emergency fatigue alert to all registered family monitors."""
        stmt = (
            select(User.fcm_token)
            .join(FamilyMember, FamilyMember.user_id == User.id)
            .where(
                FamilyMember.family_id == family_id,
                User.fcm_token.is_not(None),
            )
        )
        tokens = [t for t in db.scalars(stmt).all() if t]
        if not tokens:
            return 0

        title = "🚨 PERINGATAN DARURAT: Pengemudi Mengantuk Berat!"
        body = (
            f"{driver_name} terdeteksi mengalami {incident_type} saat mengemudi "
            f"{vehicle_name} di kecepatan {speed_kmh:.1f} km/jam! Segera hubungi pengemudi."
        )
        data = {
            "type": "EMERGENCY_FATIGUE_ALERT",
            "family_id": str(family_id),
            "driver_name": driver_name,
            "vehicle_name": vehicle_name,
            "incident_type": incident_type,
            "speed_kmh": f"{speed_kmh:.1f}",
            "lat": str(lat) if lat is not None else "",
            "lng": str(lng) if lng is not None else "",
        }

        return self.send_notification_to_tokens(
            tokens=tokens, title=title, body=body, data=data
        )


fcm_notifier = FCMNotifierService()

