"""WebSocket broadcaster for real-time mobile family live map telemetry."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.family import FamilyMember

logger = logging.getLogger("winfams-api.ws")
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages active WebSocket connections grouped by family ID."""

    def __init__(self) -> None:
        self._active_connections: dict[int, set[WebSocket]] = {}

    async def connect(self, family_id: int, websocket: WebSocket) -> None:
        """Accept WebSocket connection and store in active connections registry."""
        await websocket.accept()
        if family_id not in self._active_connections:
            self._active_connections[family_id] = set()
        self._active_connections[family_id].add(websocket)
        logger.info(
            "WebSocket client connected to family %d (Active: %d)",
            family_id,
            len(self._active_connections[family_id]),
        )

    def disconnect(self, family_id: int, websocket: WebSocket) -> None:
        """Remove WebSocket connection from active connections registry."""
        if family_id in self._active_connections:
            self._active_connections[family_id].discard(websocket)
            if not self._active_connections[family_id]:
                del self._active_connections[family_id]
        logger.info("WebSocket client disconnected from family %d", family_id)

    async def broadcast_to_family(
        self, family_id: int, message: dict[str, Any]
    ) -> int:
        """Broadcast JSON message to all connected clients in the family channel."""
        connections = self._active_connections.get(family_id)
        if not connections:
            return 0

        dead_connections: list[WebSocket] = []
        sent_count = 0

        for ws in list(connections):
            try:
                await ws.send_json(message)
                sent_count += 1
            except Exception:
                dead_connections.append(ws)

        for ws in dead_connections:
            self.disconnect(family_id, ws)

        return sent_count

    def get_active_count(self, family_id: int) -> int:
        """Return the count of active WebSocket clients for a family."""
        return len(self._active_connections.get(family_id, set()))


connection_manager = ConnectionManager()


@router.websocket("/ws/families/{family_id}")
async def family_live_map_ws(
    websocket: WebSocket,
    family_id: int,
    token: str | None = Query(None),
    db: Session = Depends(get_db),
) -> None:
    """Real-time WebSocket channel streaming vehicle movement and alerts to mobile apps."""
    if not token:
        logger.warning("Rejected WS connection: Missing token for family %d", family_id)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        logger.warning("Rejected WS connection: Invalid JWT for family %d", family_id)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify user is a member of this family
    membership = db.scalar(
        select(FamilyMember).where(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == user_id,
        )
    )
    if membership is None:
        logger.warning(
            "Rejected WS: User %d not member of family %d", user_id, family_id
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await connection_manager.connect(family_id, websocket)

    # Send initial handshake acknowledging connection
    await websocket.send_json(
        {
            "type": "CONNECTION_ESTABLISHED",
            "family_id": family_id,
            "user_id": user_id,
            "server_time": datetime.now(timezone.utc).isoformat(),
        }
    )

    try:
        while True:
            text = await websocket.receive_text()
            if text.strip().lower() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        connection_manager.disconnect(family_id, websocket)
    except Exception as e:
        logger.debug("WebSocket terminated: %s", e)
        connection_manager.disconnect(family_id, websocket)

