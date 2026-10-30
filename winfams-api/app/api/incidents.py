"""Family fatigue incident history and querying endpoints."""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.family import FamilyMember
from app.models.incident import FatigueIncident
from app.models.user import User
from app.schemas.edge import IncidentResponse

logger = logging.getLogger("winfams-api.incidents")
router = APIRouter(tags=["Incident History"])


def format_incident_response(inc: FatigueIncident) -> IncidentResponse:
    """Format FatigueIncident ORM entity into IncidentResponse schema."""
    d_uid = inc.device.device_uid if inc.device else "unknown"
    v_name = inc.device.vehicle_name if inc.device else "unknown"
    dr_name = inc.driver.name if inc.driver else None
    return IncidentResponse(
        id=inc.id,
        device_id=inc.device_id,
        device_uid=d_uid,
        vehicle_name=v_name,
        driver_id=inc.driver_id,
        driver_name=dr_name,
        family_id=inc.family_id,
        incident_type=inc.incident_type,
        confidence_score=inc.confidence_score,
        duration_seconds=inc.duration_seconds,
        lat=inc.lat,
        lng=inc.lng,
        speed_kmh=inc.speed_kmh,
        recorded_at=inc.recorded_at,
        created_at=inc.created_at,
    )


@router.get(
    "/families/{family_id}/incidents",
    response_model=list[IncidentResponse],
    summary="Retrieve fatigue incident history for a family",
)
def get_family_incidents(
    family_id: int,
    driver_id: int | None = Query(None, description="Filter by driver ID"),
    incident_type: str | None = Query(None, description="Filter by incident type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IncidentResponse]:
    """List historical fatigue incidents for family members with optional filters."""
    membership = db.scalar(
        select(FamilyMember).where(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Anda bukan anggota dari grup keluarga ini.",
        )

    stmt = (
        select(FatigueIncident)
        .options(
            selectinload(FatigueIncident.device),
            selectinload(FatigueIncident.driver),
        )
        .where(FatigueIncident.family_id == family_id)
    )
    if driver_id is not None:
        stmt = stmt.where(FatigueIncident.driver_id == driver_id)
    if incident_type is not None:
        stmt = stmt.where(FatigueIncident.incident_type == incident_type)

    stmt = stmt.order_by(FatigueIncident.recorded_at.desc()).offset(offset).limit(limit)
    incidents = db.scalars(stmt).all()

    return [format_incident_response(inc) for inc in incidents]

