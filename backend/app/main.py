# Pfad: /backend/app/main.py
"""
FlowAudit FastAPI Application

Haupteinstiegspunkt für die Backend-API.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __description__, __version__
from app.api import (
    documents,
    export,
    feedback,
    generator,
    health,
    llm,
    projects,
    rag,
    rulesets,
    settings,
    stats,
    system,
)
from app.config import get_settings
from app.database import close_db, init_db

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

config = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Handler.

    Initialisiert und schließt Ressourcen.
    """
    logger.info("Starting FlowAudit Backend...")

    # Datenbank initialisieren
    await init_db()
    logger.info("Database initialized")

    # Storage-Verzeichnisse erstellen
    for path in [
        config.uploads_path,
        config.exports_path,
        config.previews_path,
        config.logs_path,
    ]:
        path.mkdir(parents=True, exist_ok=True)
    logger.info("Storage directories created")

    yield

    # Cleanup
    await close_db()
    logger.info("FlowAudit Backend shutdown complete")


# FastAPI App erstellen
app = FastAPI(
    title="FlowAudit API",
    description=__description__,
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Globaler Exception-Handler für RFC 7807 Problem Details."""
    logger.exception(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://flowaudit.local/problems/internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": str(exc) if config.debug else "An unexpected error occurred",
            "instance": str(request.url),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# API Router registrieren
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(settings.router, prefix="/api", tags=["Settings"])
app.include_router(rulesets.router, prefix="/api", tags=["Rulesets"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(llm.router, prefix="/api", tags=["LLM"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])
app.include_router(rag.router, prefix="/api", tags=["RAG"])
app.include_router(stats.router, prefix="/api", tags=["Statistics"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(generator.router, prefix="/api", tags=["Generator"])
app.include_router(system.router, prefix="/api", tags=["System"])


@app.get("/", include_in_schema=False)
async def root() -> dict[str, Any]:
    """Root-Endpoint mit API-Info."""
    return {
        "name": "FlowAudit API",
        "version": __version__,
        "docs": "/api/docs",
        "health": "/api/health",
    }
