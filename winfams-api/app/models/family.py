"""Family and FamilyMember ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.device import Device
    from app.models.incident import FatigueIncident


class Family(Base):
    """Family group entity linking family members and registered IoT devices."""

    __tablename__ = "families"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    invite_code: Mapped[str] = mapped_column(
        String(12), unique=True, index=True, nullable=False
    )
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    creator: Mapped[User] = relationship("User", back_populates="families_created")
    members: Mapped[List[FamilyMember]] = relationship(
        "FamilyMember", back_populates="family", cascade="all, delete-orphan"
    )
    devices: Mapped[List[Device]] = relationship(
        "Device", back_populates="family"
    )
    incidents: Mapped[List[FatigueIncident]] = relationship(
        "FatigueIncident", back_populates="family", cascade="all, delete-orphan"
    )


class FamilyMember(Base):
    """Pivot model connecting users with family groups along with authorization roles."""

    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(20), default="MONITOR", nullable=False
    )  # 'DRIVER', 'MONITOR', 'ADMIN'
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    family: Mapped[Family] = relationship("Family", back_populates="members")
    user: Mapped[User] = relationship("User", back_populates="family_memberships")

