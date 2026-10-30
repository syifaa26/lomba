"""Pydantic schemas for Edge telemetry ingestion and incident records."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class LocationSchema(BaseModel):
    """Geographic coordinates and movement telemetry."""

    lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    lng: float | None = Field(default=None, ge=-180.0, le=180.0)
    speed_kmh: float = Field(default=0.0, ge=0.0)
    heading: float = Field(default=0.0, ge=0.0, le=360.0)


class HeartbeatRequest(BaseModel):
    """Payload received from Raspberry Pi periodic telemetry heartbeat."""

    device_uid: str = Field(..., min_length=4, max_length=64)
    state: str = Field(default="NORMAL", max_length=32)
    drowsy_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    yawn_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    location: LocationSchema = Field(default_factory=LocationSchema)
    timestamp: int | float | None = None


class HeartbeatResponse(BaseModel):
    """Heartbeat acknowledgement payload."""

    status: str = "ok"
    device_uid: str
    state: str
    acknowledged_at: datetime


class IncidentCreateRequest(BaseModel):
    """Payload sent by Raspberry Pi upon detecting fatigue or during offline flush."""

    device_uid: str = Field(..., min_length=4, max_length=64)
    incident_type: str = Field(
        ..., pattern="^(WARNING_FATIGUE|CRITICAL_DROWSY|DROWSY|YAWN)$"
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    duration_seconds: float = Field(..., ge=0.0)
    location: LocationSchema = Field(default_factory=LocationSchema)
    recorded_at: int | float | datetime


class IncidentResponse(BaseModel):
    """Representation of a recorded driver fatigue incident."""

    id: int
    device_id: int
    device_uid: str
    vehicle_name: str
    driver_id: int | None = None
    driver_name: str | None = None
    family_id: int
    incident_type: str
    confidence_score: float
    duration_seconds: float
    lat: float | None = None
    lng: float | None = None
    speed_kmh: float = 0.0
    recorded_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

