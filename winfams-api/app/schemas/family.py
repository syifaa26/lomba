"""Pydantic schemas for family group management and device pairing."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class FamilyCreateRequest(BaseModel):
    """Payload for creating a new family group."""

    name: str = Field(..., min_length=2, max_length=100)


class FamilyJoinRequest(BaseModel):
    """Payload for joining an existing family via invite code."""

    invite_code: str = Field(..., min_length=6, max_length=12)
    role: str = Field(default="MONITOR", pattern="^(DRIVER|MONITOR|ADMIN|MEMBER)$")


class FamilyResponse(BaseModel):
    """Family group summary response."""

    id: int
    name: str
    invite_code: str
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FamilyMemberResponse(BaseModel):
    """Family member representation with user details and assigned role."""

    id: int
    user_id: int
    name: str
    email: str
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceRegisterRequest(BaseModel):
    """Payload for pairing an IoT edge device (Raspberry Pi 4) to a family."""

    device_uid: str = Field(..., min_length=4, max_length=64)
    vehicle_name: str = Field(default="Kendaraan Keluarga", max_length=100)
    api_key: str = Field(default="", description="Secret API key for the device")


class DeviceResponse(BaseModel):
    """IoT Edge device telemetry and status representation."""

    id: int
    device_uid: str
    vehicle_name: str
    is_online: bool
    current_state: str
    last_lat: float | None = None
    last_lng: float | None = None
    last_speed_kmh: float = 0.0
    last_seen_at: datetime | None = None
    active_driver_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class FamilyOverviewResponse(BaseModel):
    """Comprehensive family status response including members and live vehicle fleet."""

    family: FamilyResponse
    members: list[FamilyMemberResponse]
    devices: list[DeviceResponse]
