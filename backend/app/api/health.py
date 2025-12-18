# Pfad: /backend/app/api/health.py
"""
FlowAudit Health & Meta API

Endpoints für Health-Check und Metadaten.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.config import get_settings
from app.database import get_async_session

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Health-Check Endpoint.

    Prüft Verfügbarkeit aller Komponenten:
    - Datenbank
    - Ollama (lokales LLM)
    - Vectorstore (ChromaDB)

    Returns:
        Health-Status mit Komponenten-Details.
    """
    services: dict[str, str] = {}

    # Database check
    try:
        await session.execute(text("SELECT 1"))
        services["db"] = "ok"
    except Exception:
        services["db"] = "error"

    # Ollama check (vereinfacht - wird später erweitert)
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_host}/api/tags")
            services["ollama"] = "ok" if response.status_code == 200 else "error"
    except Exception:
        services["ollama"] = "error"

    # ChromaDB check (vereinfacht - wird später erweitert)
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"http://{settings.chroma_host}:{settings.chroma_port}/api/v2/heartbeat"
            )
            services["vectorstore"] = "ok" if response.status_code == 200 else "error"
    except Exception:
        services["vectorstore"] = "error"

    # Overall status
    overall_status = "ok" if all(v == "ok" for v in services.values()) else "degraded"

    return {
        "status": overall_status,
        "time_utc": datetime.now(UTC).isoformat(),
        "version": __version__,
        "services": services,
    }


@router.get("/meta")
async def get_meta(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Meta-Informationen.

    Liefert UI-Infos und Zähler für Dashboard.

    Returns:
        Meta-Informationen mit Counters.
    """
    from sqlalchemy import func, select

    from app.models import Document, Project, RagExample

    # Counts abfragen
    projects_total = await session.scalar(select(func.count(Project.id))) or 0
    documents_total = await session.scalar(select(func.count(Document.id))) or 0
    rag_examples_total = await session.scalar(select(func.count(RagExample.id))) or 0

    # Aktive Einstellungen laden (später aus Settings-Tabelle)
    return {
        "active": {
            "ruleset_id": "DE_USTG",
            "ruleset_version": "1.0.0",
            "ui_language": "de",
            "provider": "LOCAL_OLLAMA",
            "model_name": settings.ollama_default_model,
        },
        "counters": {
            "projects_total": projects_total,
            "documents_total": documents_total,
            "documents_session": 0,  # Session-spezifisch, später implementieren
            "rag_examples_total": rag_examples_total,
        },
    }
