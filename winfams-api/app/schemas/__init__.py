"""Pydantic validation schemas package."""

from app.schemas.auth import (
    FCMTokenUpdateRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.edge import (
    HeartbeatRequest,
    HeartbeatResponse,
    IncidentCreateRequest,
    IncidentResponse,
    LocationSchema,
)
from app.schemas.family import (
    DeviceRegisterRequest,
    DeviceResponse,
    FamilyCreateRequest,
    FamilyJoinRequest,
    FamilyMemberResponse,
    FamilyOverviewResponse,
    FamilyResponse,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "FCMTokenUpdateRequest",
    "FamilyCreateRequest",
    "FamilyJoinRequest",
    "FamilyResponse",
    "FamilyMemberResponse",
    "DeviceRegisterRequest",
    "DeviceResponse",
    "FamilyOverviewResponse",
    "LocationSchema",
    "HeartbeatRequest",
    "HeartbeatResponse",
    "IncidentCreateRequest",
    "IncidentResponse",
]
