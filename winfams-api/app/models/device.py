"""Device ORM model representing Raspberry Pi edge unit."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.family import Family
    from app.models.user import User
    from app.models.incident import FatigueIncident


class Device(Base):
    """IoT Edge device entity tracking vehicle telematics and driver alertness state."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_uid: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    family_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("families.id", ondelete="SET NULL"), index=True, nullable=True
    )
    active_driver_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    vehicle_name: Mapped[str] = mapped_column(
        String(100), default="Kendaraan Keluarga", nullable=False
    )
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_state: Mapped[str] = mapped_column(
        String(32), default="IDLE", nullable=False
    )  # 'IDLE', 'DRIVING', 'WARNING_FATIGUE', 'CRITICAL_DROWSY'
    last_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_speed_kmh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    family: Mapped[Family | None] = relationship("Family", back_populates="devices")
    active_driver: Mapped[User | None] = relationship(
        "User", back_populates="active_devices"
    )
    incidents: Mapped[List[FatigueIncident]] = relationship(
        "FatigueIncident", back_populates="device", cascade="all, delete-orphan"
    )

