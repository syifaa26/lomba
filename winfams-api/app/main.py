"""WinFams FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 - ensure all models are registered with Base.metadata
from app.api import (
    auth_router,
    edge_router,
    families_router,
    incidents_router,
    ws_router,
)
from app.core.config import settings
from app.core.database import Base, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("winfams-api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager initializing database tables on startup."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down WinFams API application.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend REST API and Real-time Notification Engine for WinFams",
    lifespan=lifespan,
)

# Enable CORS for mobile application and edge clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(families_router, prefix=settings.API_V1_STR)
app.include_router(edge_router, prefix=settings.API_V1_STR)
app.include_router(incidents_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)


@app.get("/", tags=["Health Check"])
def root_status() -> dict[str, str]:
    """Root endpoint verifying API availability."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get("/health", tags=["Health Check"])
def health_check() -> dict[str, str]:
    """Health check endpoint for Docker and cloud monitoring."""
    return {"status": "healthy"}
