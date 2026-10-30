"""Data transfer objects for WinFams Edge strictly following winfams_prd.md."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class LocationData:
    """Geographic location and movement telemetry."""

    lat: float | None = None
    lng: float | None = None
    speed_kmh: float = 0.0
    heading: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lng": self.lng,
            "speed_kmh": round(self.speed_kmh, 2),
            "heading": round(self.heading, 2),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LocationData:
        return cls(
            lat=float(data["lat"]) if data.get("lat") is not None else None,
            lng=float(data["lng"]) if data.get("lng") is not None else None,
            speed_kmh=float(data.get("speed_kmh", 0.0)),
            heading=float(data.get("heading", 0.0)),
        )


@dataclass
class HeartbeatPayload:
    """Telemetry heartbeat sent periodically to FastAPI POST /api/v1/edge/heartbeat."""

    device_uid: str
    state: str
    drowsy_confidence: float
    yawn_confidence: float
    location: LocationData
    timestamp: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_uid": self.device_uid,
            "state": self.state,
            "drowsy_confidence": round(self.drowsy_confidence, 4),
            "yawn_confidence": round(self.yawn_confidence, 4),
            "location": self.location.to_dict(),
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HeartbeatPayload:
        raw_loc = data.get("location", {})
        location = (
            LocationData.from_dict(raw_loc)
            if isinstance(raw_loc, dict)
            else LocationData()
        )
        return cls(
            device_uid=str(data["device_uid"]),
            state=str(data.get("state", "NORMAL")),
            drowsy_confidence=float(data.get("drowsy_confidence", 0.0)),
            yawn_confidence=float(data.get("yawn_confidence", 0.0)),
            location=location,
            timestamp=int(data.get("timestamp", 0)),
        )

    @classmethod
    def from_json(cls, json_str: str) -> HeartbeatPayload:
        return cls.from_dict(json.loads(json_str))


@dataclass
class IncidentPayload:
    """Incident payload sent to FastAPI POST /api/v1/edge/incidents and offline queue."""

    device_uid: str
    incident_type: str
    confidence_score: float
    duration_seconds: float
    location: LocationData
    recorded_at: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_uid": self.device_uid,
            "incident_type": self.incident_type,
            "confidence_score": round(self.confidence_score, 4),
            "duration_seconds": round(self.duration_seconds, 2),
            "location": self.location.to_dict(),
            "recorded_at": self.recorded_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IncidentPayload:
        raw_loc = data.get("location", {})
        location = (
            LocationData.from_dict(raw_loc)
            if isinstance(raw_loc, dict)
            else LocationData()
        )
        return cls(
            device_uid=str(data["device_uid"]),
            incident_type=str(data["incident_type"]),
            confidence_score=float(data.get("confidence_score", 0.0)),
            duration_seconds=float(data.get("duration_seconds", 0.0)),
            location=location,
            recorded_at=int(data.get("recorded_at", 0)),
        )

    @classmethod
    def from_json(cls, json_str: str) -> IncidentPayload:
        return cls.from_dict(json.loads(json_str))


@dataclass
class DeviceStatus:
    """Device status model maintaining compatibility across Edge modules."""

    device_id: str
    driver_uid: str
    is_online: bool
    state: str
    drowsy_confidence: float
    yawn_confidence: float
    location: LocationData
    last_updated: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "driver_uid": self.driver_uid,
            "is_online": self.is_online,
            "state": self.state,
            "drowsy_confidence": round(self.drowsy_confidence, 4),
            "yawn_confidence": round(self.yawn_confidence, 4),
            "location": self.location.to_dict(),
            "last_updated": self.last_updated,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceStatus:
        raw_loc = data.get("location", {})
        location = (
            LocationData.from_dict(raw_loc)
            if isinstance(raw_loc, dict)
            else LocationData()
        )
        return cls(
            device_id=str(data.get("device_id", data.get("device_uid", ""))),
            driver_uid=str(data.get("driver_uid", "")),
            is_online=bool(data.get("is_online", False)),
            state=str(data.get("state", "UNKNOWN")),
            drowsy_confidence=float(data.get("drowsy_confidence", 0.0)),
            yawn_confidence=float(data.get("yawn_confidence", 0.0)),
            location=location,
            last_updated=int(data.get("last_updated", data.get("timestamp", 0))),
        )

    @classmethod
    def from_json(cls, json_str: str) -> DeviceStatus:
        return cls.from_dict(json.loads(json_str))


@dataclass
class FatigueIncident:
    """Fatigue incident model maintaining compatibility across Edge modules."""

    incident_id: str
    device_id: str
    driver_uid: str
    family_group_id: str
    type: str
    confidence_score: float
    duration_seconds: float
    location: LocationData
    timestamp: int
    resolved: bool = False

    def to_incident_payload(self) -> IncidentPayload:
        """Convert FatigueIncident to API IncidentPayload."""
        return IncidentPayload(
            device_uid=self.device_id,
            incident_type=self.type,
            confidence_score=self.confidence_score,
            duration_seconds=self.duration_seconds,
            location=self.location,
            recorded_at=self.timestamp,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "device_id": self.device_id,
            "driver_uid": self.driver_uid,
            "family_group_id": self.family_group_id,
            "type": self.type,
            "confidence_score": round(self.confidence_score, 4),
            "duration_seconds": round(self.duration_seconds, 2),
            "location": self.location.to_dict(),
            "timestamp": self.timestamp,
            "resolved": self.resolved,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FatigueIncident:
        raw_loc = data.get("location", {})
        location = (
            LocationData.from_dict(raw_loc)
            if isinstance(raw_loc, dict)
            else LocationData()
        )
        return cls(
            incident_id=str(data.get("incident_id", "")),
            device_id=str(data.get("device_id", data.get("device_uid", ""))),
            driver_uid=str(data.get("driver_uid", "")),
            family_group_id=str(data.get("family_group_id", "")),
            type=str(data.get("type", data.get("incident_type", ""))),
            confidence_score=float(data.get("confidence_score", 0.0)),
            duration_seconds=float(data.get("duration_seconds", 0.0)),
            location=location,
            timestamp=int(data.get("timestamp", data.get("recorded_at", 0))),
            resolved=bool(data.get("resolved", False)),
        )

    @classmethod
    def from_json(cls, json_str: str) -> FatigueIncident:
        return cls.from_dict(json.loads(json_str))
