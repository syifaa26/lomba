"""User ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.family import Family, FamilyMember
    from app.models.device import Device
    from app.models.incident import FatigueIncident


class User(Base):
    """User account entity storing authentication credentials and FCM tokens."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(120), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    fcm_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    families_created: Mapped[List[Family]] = relationship(
        "Family", back_populates="creator", cascade="all, delete-orphan"
    )
    family_memberships: Mapped[List[FamilyMember]] = relationship(
        "FamilyMember", back_populates="user", cascade="all, delete-orphan"
    )
    active_devices: Mapped[List[Device]] = relationship(
        "Device", back_populates="active_driver"
    )
    incidents: Mapped[List[FatigueIncident]] = relationship(
        "FatigueIncident", back_populates="driver"
    )

