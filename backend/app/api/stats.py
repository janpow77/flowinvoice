# Pfad: /backend/app/api/stats.py
"""
FlowAudit Statistics API

Endpoints für Dashboard-Statistiken.
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.document import Document
from app.models.feedback import Feedback, RagExample
from app.models.llm import LlmRun
from app.models.project import Project
from app.schemas.stats import (
    FeedbackStatsResponse,
    GlobalStatsResponse,
    LlmStatsResponse,
    ProjectStatsResponse,
    RagStatsResponse,
    SystemStatsResponse,
)

router = APIRouter()


@router.get("/stats/global")
async def get_global_stats(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Globale Statistiken für Dashboard.

    Returns:
        Übersicht, Genauigkeit, Provider-Stats.
    """
    # Counts
    total_projects = await session.scalar(select(func.count(Project.id))) or 0
    total_documents = await session.scalar(select(func.count(Document.id))) or 0
    total_rag_examples = await session.scalar(select(func.count(RagExample.id))) or 0
    total_llm_runs = await session.scalar(select(func.count(LlmRun.id))) or 0

    return {
        "overview": {
            "total_analyses": total_llm_runs,
            "total_projects": total_projects,
            "total_documents": total_documents,
            "total_rag_examples": total_rag_examples,
            "session_analyses": 0,
            "uptime_hours": 0.0,
        },
        "accuracy": {
            "overall_accuracy_percent": 0.0,
            "feature_accuracy": {},
        },
        "by_provider": {},
        "time_trend": None,
    }


@router.get("/projects/{project_id}/stats")
async def get_project_stats(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Projekt-Statistiken.

    Args:
        project_id: Projekt-ID

    Returns:
        Zähler, Timing, Token-Stats.
    """
    # Document counts
    total_docs = await session.scalar(
        select(func.count(Document.id)).where(Document.project_id == project_id)
    ) or 0

    return {
        "project_id": project_id,
        "counters": {
            "documents_total": total_docs,
            "accepted": 0,
            "review_pending": 0,
            "rejected": 0,
            "rag_examples_used": 0,
        },
        "timings": {
            "avg_parse_ms": 0,
            "avg_llm_ms": 0,
            "avg_total_ms": 0,
        },
        "tokens": {
            "avg_in": 0,
            "avg_out": 0,
        },
        "feature_error_rates": [],
    }


@router.get("/stats/feedback")
async def get_feedback_stats(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Feedback-Statistiken.

    Returns:
        Bewertungsverteilung, Fehler nach Feature/Quelle.
    """
    total_feedback = await session.scalar(select(func.count(Feedback.id))) or 0

    return {
        "summary": {
            "total_feedback_entries": total_feedback,
            "rating_distribution": {
                "CORRECT": 0,
                "PARTIAL": 0,
                "WRONG": 0,
            },
            "avg_corrections_per_analysis": 0.0,
        },
        "errors_by_feature": [],
        "errors_by_source": {
            "TAX_LAW": {
                "label_de": "Steuerrecht (UStG/VAT/MwStSystRL)",
                "label_en": "Tax Law",
                "total_errors": 0,
                "percentage": 0.0,
                "features": [],
                "detail": [],
            },
            "BENEFICIARY_DATA": {
                "label_de": "Begünstigten-Daten",
                "label_en": "Beneficiary Data",
                "total_errors": 0,
                "percentage": 0.0,
                "features": [],
            },
            "LOCATION_VALIDATION": {
                "label_de": "Standort-Validierung",
                "label_en": "Location Validation",
                "total_errors": 0,
                "percentage": 0.0,
                "features": [],
            },
        },
        "rag_improvement": {
            "accuracy_before_rag": 0.0,
            "accuracy_after_rag": 0.0,
            "improvement_percent": 0.0,
            "examples_contributing": 0,
        },
        "feedback_timeline": [],
    }


@router.get("/stats/llm")
async def get_llm_stats(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    LLM-Statistiken.

    Returns:
        Modell-Stats, Ressourcen-Nutzung.
    """
    total_llm_runs = await session.scalar(select(func.count(LlmRun.id))) or 0

    return {
        "active_provider": "LOCAL_OLLAMA",
        "active_model": "llama3.1:8b-instruct-q4",
        "local_model_stats": {
            "model_name": "llama3.1:8b-instruct-q4",
            "model_size_gb": 4.7,
            "quantization": "Q4_K_M",
            "loaded": False,
            "context_window": 8192,
            "total_requests": total_llm_runs,
            "avg_tokens_in": 0,
            "avg_tokens_out": 0,
            "total_tokens_processed": 0,
            "avg_inference_time_ms": 0,
            "min_inference_time_ms": 0,
            "max_inference_time_ms": 0,
            "tokens_per_second_avg": 0.0,
        },
        "resource_usage": {
            "current_cpu_percent": 0.0,
            "current_ram_mb": 0,
            "current_ram_percent": 0.0,
            "gpu_available": False,
            "gpu_name": None,
            "gpu_memory_used_mb": 0,
            "gpu_memory_total_mb": 0,
            "gpu_utilization_percent": 0.0,
        },
        "error_stats": {
            "timeout_count": 0,
            "parse_error_count": 0,
            "connection_error_count": 0,
            "last_error": None,
        },
        "external_providers": {},
    }


@router.get("/stats/rag")
async def get_rag_stats(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    RAG-Statistiken.

    Returns:
        Collection-Stats, Retrieval-Stats.
    """
    total_examples = await session.scalar(select(func.count(RagExample.id))) or 0

    return {
        "collection_stats": {
            "collection_name": "flowaudit_corrections",
            "total_examples": total_examples,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_dimension": 384,
            "storage_size_mb": 0.0,
        },
        "by_ruleset": {},
        "by_feature": [],
        "retrieval_stats": {
            "total_retrievals": 0,
            "avg_similarity_score": 0.0,
            "cache_hit_rate": 0.0,
        },
        "recent_examples": [],
    }


@router.get("/stats/system")
async def get_system_stats(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    System-Statistiken.

    Returns:
        Komponenten-Status, Speicher-Info.
    """
    import psutil

    # System-Info
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "components": {
            "backend": {
                "status": "ok",
                "version": "0.1.0",
                "uptime_sec": 0,
            },
            "database": {
                "status": "ok",
                "type": "PostgreSQL",
                "version": "16",
                "connections_active": 0,
                "connections_max": 100,
            },
            "ollama": {
                "status": "unknown",
                "version": None,
                "models_loaded": 0,
            },
            "chromadb": {
                "status": "unknown",
                "version": None,
                "collections": 0,
            },
            "redis": {
                "status": "unknown",
                "version": None,
                "memory_used_mb": 0,
            },
        },
        "storage": {
            "db_size_mb": 0.0,
            "uploads_size_mb": 0.0,
            "generated_size_mb": 0.0,
            "vectorstore_size_mb": 0.0,
            "logs_size_mb": 0.0,
            "total_used_mb": disk.used / (1024 * 1024),
            "disk_free_mb": disk.free / (1024 * 1024),
        },
        "activity_log": [],
    }
