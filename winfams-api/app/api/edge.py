"""Edge telemetry ingestion and real-time alert dispatch endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.incidents import format_incident_response
from app.api.ws import connection_manager
from app.core.database import get_db
from app.core.security import hash_api_key
from app.models.device import Device
from app.models.incident import FatigueIncident
from app.schemas.edge import (
    HeartbeatRequest,
    HeartbeatResponse,
    IncidentCreateRequest,
    IncidentResponse,
)
from app.services.fcm_notifier import fcm_notifier

logger = logging.getLogger("winfams-api.edge")
router = APIRouter(tags=["Edge Telemetry & Incidents"])


def parse_timestamp(ts: int | float | datetime | None) -> datetime:
    """Parse integer/float unix timestamp or datetime into timezone-aware datetime."""
    if ts is None:
        return datetime.now(timezone.utc)
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(ts, datetime):
        return ts if ts.tzinfo is not None else ts.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def authenticate_edge_device(
    x_device_api_key: str | None = Header(None, alias="X-Device-API-Key"),
    db: Session = Depends(get_db),
) -> Device:
    """Validate device API key from X-Device-API-Key header."""
    if not x_device_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header 'X-Device-API-Key' diperlukan untuk mengakses layanan Edge.",
        )
    key_hash = hash_api_key(x_device_api_key)
    device = db.scalar(select(Device).where(Device.api_key_hash == key_hash))
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kunci API perangkat tidak valid atau belum terdaftar.",
        )
    return device


@router.post(
    "/edge/heartbeat",
    response_model=HeartbeatResponse,
    summary="Receive periodic telemetry heartbeat from Raspberry Pi 4",
)
async def receive_heartbeat(
    payload: HeartbeatRequest,
    device: Device = Depends(authenticate_edge_device),
    db: Session = Depends(get_db),
) -> HeartbeatResponse:
    """Update device state, GPS coordinates, speed, and broadcast to family."""
    if payload.device_uid != device.device_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device UID tidak cocok dengan kredensial API Key yang diberikan.",
        )

    now = datetime.now(timezone.utc)
    device.is_online = True
    device.current_state = payload.state
    device.last_seen_at = now
    if payload.location is not None:
        if payload.location.lat is not None:
            device.last_lat = payload.location.lat
        if payload.location.lng is not None:
            device.last_lng = payload.location.lng
        device.last_speed_kmh = payload.location.speed_kmh

    db.commit()
    db.refresh(device)

    # Broadcast real-time telemetry to connected family members
    if device.family_id is not None:
        driver_name = device.active_driver.name if device.active_driver else None
        await connection_manager.broadcast_to_family(
            device.family_id,
            {
                "type": "DEVICE_TELEMETRY",
                "family_id": device.family_id,
                "device_uid": device.device_uid,
                "vehicle_name": device.vehicle_name,
                "driver_name": driver_name,
                "state": device.current_state,
                "location": {
                    "lat": device.last_lat,
                    "lng": device.last_lng,
                    "speed_kmh": device.last_speed_kmh,
                },
                "timestamp": now.isoformat(),
            },
        )

    return HeartbeatResponse(
        status="ok",
        device_uid=device.device_uid,
        state=device.current_state,
        acknowledged_at=now,
    )


@router.post(
    "/edge/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record fatigue incident, broadcast to WebSocket, and send FCM alert",
)
async def record_incident(
    payload: IncidentCreateRequest,
    device: Device = Depends(authenticate_edge_device),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """Save incident to SQL table, dispatch WS alert, and fire FCM notification."""
    if payload.device_uid != device.device_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device UID tidak cocok dengan kredensial API Key yang diberikan.",
        )
    if device.family_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Perangkat belum di-pairing ke grup keluarga mana pun.",
        )

    recorded_dt = parse_timestamp(payload.recorded_at)
    now = datetime.now(timezone.utc)

    device.is_online = True
    device.current_state = payload.incident_type
    device.last_seen_at = now
    if payload.location is not None:
        if payload.location.lat is not None:
            device.last_lat = payload.location.lat
        if payload.location.lng is not None:
            device.last_lng = payload.location.lng
        device.last_speed_kmh = payload.location.speed_kmh

    incident = FatigueIncident(
        device_id=device.id,
        driver_id=device.active_driver_id,
        family_id=device.family_id,
        incident_type=payload.incident_type,
        confidence_score=payload.confidence_score,
        duration_seconds=payload.duration_seconds,
        lat=payload.location.lat if payload.location else None,
        lng=payload.location.lng if payload.location else None,
        speed_kmh=payload.location.speed_kmh if payload.location else 0.0,
        recorded_at=recorded_dt,
        created_at=now,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # 1. Real-time WebSocket broadcast to family members
    driver_name = device.active_driver.name if device.active_driver else None
    await connection_manager.broadcast_to_family(
        device.family_id,
        {
            "type": "FATIGUE_ALERT",
            "family_id": device.family_id,
            "incident_id": incident.id,
            "device_uid": device.device_uid,
            "vehicle_name": device.vehicle_name,
            "driver_name": driver_name,
            "incident_type": incident.incident_type,
            "confidence_score": incident.confidence_score,
            "duration_seconds": incident.duration_seconds,
            "location": {
                "lat": incident.lat,
                "lng": incident.lng,
                "speed_kmh": incident.speed_kmh,
            },
            "recorded_at": incident.recorded_at.isoformat(),
        },
    )

    # 2. Push Notification via FCM
    fcm_notifier.send_emergency_fatigue_alert(
        db=db,
        family_id=device.family_id,
        driver_name=driver_name or "Pengemudi",
        vehicle_name=device.vehicle_name,
        incident_type=incident.incident_type,
        speed_kmh=incident.speed_kmh,
        lat=incident.lat,
        lng=incident.lng,
    )

    return format_incident_response(incident)
