"""API route registration and router exports."""

from __future__ import annotations

from app.api.auth import router as auth_router
from app.api.edge import router as edge_router
from app.api.families import router as families_router
from app.api.incidents import router as incidents_router
from app.api.ws import router as ws_router

__all__ = [
    "auth_router",
    "edge_router",
    "families_router",
    "incidents_router",
    "ws_router",
]
