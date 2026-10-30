"""FatigueIncident ORM model for storing drowsiness & yawning occurrences."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.family import Family
    from app.models.user import User


class FatigueIncident(Base):
    """Historical driver fatigue incident log entity."""

    __tablename__ = "fatigue_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True, nullable=False
    )
    driver_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    family_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=False
    )
    incident_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # 'WARNING_FATIGUE' or 'CRITICAL_DROWSY'
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_kmh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    device: Mapped[Device] = relationship("Device", back_populates="incidents")
    driver: Mapped[User | None] = relationship("User", back_populates="incidents")
    family: Mapped[Family] = relationship("Family", back_populates="incidents")

