"""Pydantic schemas for authentication and user management."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Payload for registering a new user."""

    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=64)
    phone_number: str = Field(default="", max_length=20)


class UserLoginRequest(BaseModel):
    """Payload for logging in."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """User profile response model."""

    id: int
    name: str
    email: str
    phone_number: str
    fcm_token: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """JWT bearer token response accompanied by user profile."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class FCMTokenUpdateRequest(BaseModel):
    """Payload for updating user FCM notification token."""

    fcm_token: str = Field(..., min_length=10)

