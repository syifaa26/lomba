"""Family management, membership, and device pairing endpoints."""

from __future__ import annotations

import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import get_current_user, hash_api_key
from app.models.device import Device
from app.models.family import Family, FamilyMember
from app.models.user import User
from app.schemas.family import (
    DeviceRegisterRequest,
    DeviceResponse,
    FamilyCreateRequest,
    FamilyJoinRequest,
    FamilyMemberResponse,
    FamilyOverviewResponse,
    FamilyResponse,
)

router = APIRouter(prefix="/families", tags=["Families"])


def generate_unique_invite_code(db: Session, length: int = 8) -> str:
    """Generate a collision-resistant uppercase alphanumeric invite code."""
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(20):
        code = "".join(secrets.choice(alphabet) for _ in range(length))
        exists = db.scalar(select(Family).where(Family.invite_code == code))
        if exists is None:
            return code
    return secrets.token_hex(4).upper()


@router.post(
    "",
    response_model=FamilyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new family group",
)
def create_family(
    payload: FamilyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FamilyResponse:
    """Create a new family group and automatically register creator as ADMIN."""
    invite_code = generate_unique_invite_code(db)
    family = Family(
        name=payload.name,
        invite_code=invite_code,
        created_by=current_user.id,
    )
    db.add(family)
    db.flush()

    member = FamilyMember(
        family_id=family.id,
        user_id=current_user.id,
        role="ADMIN",
    )
    db.add(member)
    db.commit()
    db.refresh(family)

    return FamilyResponse.model_validate(family)


@router.post(
    "/join",
    response_model=FamilyResponse,
    summary="Join an existing family group via invite code",
)
def join_family(
    payload: FamilyJoinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FamilyResponse:
    """Join a family using a valid 8-character invite code."""
    family = db.scalar(
        select(Family).where(Family.invite_code == payload.invite_code.upper().strip())
    )
    if family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kode undangan keluarga tidak ditemukan.",
        )

    existing_membership = db.scalar(
        select(FamilyMember).where(
            FamilyMember.family_id == family.id,
            FamilyMember.user_id == current_user.id,
        )
    )
    if existing_membership is not None:
        return FamilyResponse.model_validate(family)

    new_member = FamilyMember(
        family_id=family.id,
        user_id=current_user.id,
        role=payload.role,
    )
    db.add(new_member)
    db.commit()
    return FamilyResponse.model_validate(family)


@router.get(
    "/my",
    response_model=list[FamilyResponse],
    summary="Get all family groups the current user belongs to",
)
def get_my_families(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FamilyResponse]:
    """Retrieve all families associated with the authenticated user."""
    stmt = (
        select(Family)
        .join(FamilyMember, FamilyMember.family_id == Family.id)
        .where(FamilyMember.user_id == current_user.id)
    )
    families = db.scalars(stmt).all()
    return [FamilyResponse.model_validate(f) for f in families]


@router.post(
    "/{family_id}/devices",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Pair a Raspberry Pi Edge device to a family",
)
def pair_device(
    family_id: int,
    payload: DeviceRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeviceResponse:
    """Pair an edge hardware unit (Raspberry Pi 4) to the specified family."""
    # Verify current user is a member of this family
    member = db.scalar(
        select(FamilyMember).where(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id,
        )
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda bukan anggota dari grup keluarga ini.",
        )

    # API Key for device: use provided or generate default
    device_key = payload.api_key or f"devkey_{secrets.token_hex(16)}"
    key_hash = hash_api_key(device_key)

    device = db.scalar(select(Device).where(Device.device_uid == payload.device_uid))
    if device is None:
        device = Device(
            device_uid=payload.device_uid,
            api_key_hash=key_hash,
            family_id=family_id,
            active_driver_id=current_user.id,
            vehicle_name=payload.vehicle_name,
        )
        db.add(device)
    else:
        device.family_id = family_id
        device.active_driver_id = current_user.id
        device.vehicle_name = payload.vehicle_name
        device.api_key_hash = key_hash

    db.commit()
    db.refresh(device)
    return DeviceResponse.model_validate(device)


@router.get(
    "/{family_id}/overview",
    response_model=FamilyOverviewResponse,
    summary="Get full overview of family members and active vehicles",
)
def get_family_overview(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FamilyOverviewResponse:
    """Retrieve family members and live telemetry of paired vehicles."""
    membership = db.scalar(
        select(FamilyMember).where(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Anda bukan anggota dari keluarga ini.",
        )

    family = db.scalar(
        select(Family)
        .options(
            selectinload(Family.members).selectinload(FamilyMember.user),
            selectinload(Family.devices),
        )
        .where(Family.id == family_id)
    )
    if family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grup keluarga tidak ditemukan.",
        )

    member_responses = [
        FamilyMemberResponse(
            id=m.id,
            user_id=m.user.id,
            name=m.user.name,
            email=m.user.email,
            role=m.role,
            joined_at=m.joined_at,
        )
        for m in family.members
    ]

    device_responses = [DeviceResponse.model_validate(d) for d in family.devices]

    return FamilyOverviewResponse(
        family=FamilyResponse.model_validate(family),
        members=member_responses,
        devices=device_responses,
    )

