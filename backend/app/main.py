# Pfad: /backend/app/main.py
"""
FlowAudit FastAPI Application

Haupteinstiegspunkt für die Backend-API.
"""

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __description__, __version__
from app.api import (
    batch_jobs,
    custom_criteria,
    document_types,
    documents,
    export,
    feedback,
    generator,
    health,
    legal,
    llm,
    projects,
    rag,
    rulesets,
    ruleset_samples,
    settings,
    solutions,
    stats,
    system,
    user_auth,
    users,
)
from app.config import get_settings
from app.database import close_db, get_session_context, init_db
from app.seeds import seed_rulesets

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

    # Seed-Daten einfuegen (nur wenn noch nicht vorhanden)
    try:
        async with get_session_context() as session:
            count = await seed_rulesets(session)
            if count > 0:
                logger.info(f"Seeded {count} rulesets")
    except Exception as e:
        logger.warning(f"Could not seed rulesets: {e}")

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

# CORS Middleware - Origins aus Konfiguration (CORS_ORIGINS env var)
# WICHTIG: allow_credentials=True ist nur sicher mit expliziten Origins, nicht mit "*"
_cors_origins = config.cors_origins_list
_allow_credentials = "*" not in _cors_origins  # Keine Credentials bei Wildcard!

if "*" in _cors_origins and not config.debug:
    logger.warning(
        "CORS ist auf '*' konfiguriert. Dies ist nur für Entwicklung geeignet. "
        "Setzen Sie CORS_ORIGINS auf explizite Origins für Produktion."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
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
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


# API Router registrieren
app.include_router(user_auth.router, prefix="/api", tags=["Authentication"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(settings.router, prefix="/api", tags=["Settings"])
app.include_router(document_types.router, prefix="/api", tags=["Document Types"])
app.include_router(rulesets.router, prefix="/api", tags=["Rulesets"])
app.include_router(ruleset_samples.router, prefix="/api", tags=["Ruleset Samples"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(llm.router, prefix="/api", tags=["LLM"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])
app.include_router(rag.router, prefix="/api", tags=["RAG"])
app.include_router(stats.router, prefix="/api", tags=["Statistics"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(generator.router, prefix="/api", tags=["Generator"])
app.include_router(solutions.router, prefix="/api", tags=["Solutions"])
app.include_router(batch_jobs.router, prefix="/api", tags=["Batch Jobs"])
app.include_router(custom_criteria.router, prefix="/api", tags=["Custom Criteria"])
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(legal.router, prefix="/api", tags=["Legal"])


@app.get("/", include_in_schema=False)
async def root() -> dict[str, Any]:
    """Root-Endpoint mit API-Info."""
    return {
        "name": "FlowAudit API",
        "version": __version__,
        "docs": "/api/docs",
        "health": "/api/health",
    }
