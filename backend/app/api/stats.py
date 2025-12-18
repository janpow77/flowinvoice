# Pfad: /backend/app/api/stats.py
"""
FlowAudit Statistics API

Endpoints für Dashboard-Statistiken.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentAdmin
from app.database import get_async_session
from app.models.document import Document
from app.models.feedback import Feedback, RagExample
from app.models.llm import LlmRun
from app.models.project import Project
from app.models.user import User
from app.schemas.user import ActiveUsersResponse
from app.services.rule_engine import RULESETS

router = APIRouter()


@router.get("/stats/feature-names/{ruleset_id}")
async def get_feature_names(
    ruleset_id: str = "DE_USTG",
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Gibt Feature-Namen für ein Regelwerk zurück.

    Liest zuerst aus der Datenbank, dann als Fallback aus den hardcodierten Definitionen.

    Args:
        ruleset_id: Regelwerk-ID (DE_USTG, EU_VAT, UK_VAT)

    Returns:
        Dict mit feature_id -> {name_de, name_en, category, required_level, legal_basis}
    """
    from app.models.ruleset import Ruleset

    result = {}

    # Zuerst aus Datenbank lesen
    db_result = await session.execute(
        select(Ruleset).where(Ruleset.ruleset_id == ruleset_id).order_by(Ruleset.version.desc())
    )
    db_ruleset = db_result.scalar_one_or_none()

    if db_ruleset and db_ruleset.features:
        # Features aus Datenbank
        for feature in db_ruleset.features:
            result[feature.get("feature_id", "")] = {
                "name_de": feature.get("name_de", feature.get("feature_id", "")),
                "name_en": feature.get("name_en", feature.get("feature_id", "")),
                "category": feature.get("category", "TEXT"),
                "required_level": feature.get("required_level", "OPTIONAL"),
                "legal_basis": feature.get("legal_basis", ""),
            }
    else:
        # Fallback: Hardcodierte Definitionen
        features = RULESETS.get(ruleset_id, RULESETS.get("DE_USTG"))
        for feature_id, feature_def in features.items():
            result[feature_id] = {
                "name_de": feature_def.name_de,
                "name_en": feature_def.name_en,
                "category": feature_def.category.value,
                "required_level": feature_def.required_level.value,
                "legal_basis": feature_def.legal_basis,
            }

    return {
        "ruleset_id": ruleset_id,
        "features": result,
        "source": "database" if db_ruleset else "builtin",
    }


@router.get("/stats/all-feature-names")
async def get_all_feature_names(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Gibt alle Feature-Namen aller Regelwerke zurück.

    Kombiniert Datenbank-Regelwerke mit hardcodierten Definitionen.

    Returns:
        Dict mit ruleset_id -> {feature_id -> feature_info}
    """
    from app.models.ruleset import Ruleset

    result = {}

    # Zuerst hardcodierte Regelwerke
    for ruleset_id, features in RULESETS.items():
        ruleset_features = {}
        for feature_id, feature_def in features.items():
            ruleset_features[feature_id] = {
                "name_de": feature_def.name_de,
                "name_en": feature_def.name_en,
                "category": feature_def.category.value,
                "required_level": feature_def.required_level.value,
                "legal_basis": feature_def.legal_basis,
            }
        result[ruleset_id] = ruleset_features

    # Dann Datenbank-Regelwerke hinzufügen/überschreiben
    db_result = await session.execute(select(Ruleset))
    db_rulesets = db_result.scalars().all()

    for db_ruleset in db_rulesets:
        if db_ruleset.features:
            ruleset_features = {}
            for feature in db_ruleset.features:
                ruleset_features[feature.get("feature_id", "")] = {
                    "name_de": feature.get("name_de", feature.get("feature_id", "")),
                    "name_en": feature.get("name_en", feature.get("feature_id", "")),
                    "category": feature.get("category", "TEXT"),
                    "required_level": feature.get("required_level", "OPTIONAL"),
                    "legal_basis": feature.get("legal_basis", ""),
                }
            # Überschreibe hardcodierte mit DB-Version
            result[db_ruleset.ruleset_id] = ruleset_features

    return {
        "rulesets": result,
    }


@router.get("/stats/global")
async def get_global_stats(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Globale Statistiken für Dashboard.

    Returns:
        Übersicht, Genauigkeit, Provider-Stats.
    """
    from app.models.enums import DocumentStatus

    # Counts
    total_projects = await session.scalar(select(func.count(Project.id))) or 0
    total_documents = await session.scalar(select(func.count(Document.id))) or 0
    total_rag_examples = await session.scalar(select(func.count(RagExample.id))) or 0
    total_llm_runs = await session.scalar(select(func.count(LlmRun.id))) or 0

    # Feedback-basierte Genauigkeit
    total_feedback = await session.scalar(select(func.count(Feedback.id))) or 0
    correct_feedback = await session.scalar(
        select(func.count(Feedback.id)).where(Feedback.rating == "CORRECT")
    ) or 0

    accuracy_percent = (
        (correct_feedback / total_feedback * 100) if total_feedback > 0 else 0.0
    )

    # Provider-Stats aus LLM-Runs
    provider_stats = {}
    provider_query = await session.execute(
        select(
            LlmRun.provider,
            func.count(LlmRun.id).label("count"),
            func.avg(LlmRun.input_tokens).label("avg_input"),
            func.avg(LlmRun.output_tokens).label("avg_output"),
        ).group_by(LlmRun.provider)
    )
    for row in provider_query.all():
        provider_name = row.provider.value if row.provider else "unknown"
        provider_stats[provider_name] = {
            "total_runs": row.count,
            "avg_input_tokens": round(row.avg_input or 0),
            "avg_output_tokens": round(row.avg_output or 0),
        }

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
            "overall_accuracy_percent": round(accuracy_percent, 1),
            "total_feedback": total_feedback,
            "correct_count": correct_feedback,
            "feature_accuracy": {},
        },
        "by_provider": provider_stats,
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
    from app.models.enums import DocumentStatus

    # Document counts by status
    total_docs = await session.scalar(
        select(func.count(Document.id)).where(Document.project_id == project_id)
    ) or 0

    accepted_docs = await session.scalar(
        select(func.count(Document.id)).where(
            Document.project_id == project_id,
            Document.status == DocumentStatus.ACCEPTED,
        )
    ) or 0

    review_pending = await session.scalar(
        select(func.count(Document.id)).where(
            Document.project_id == project_id,
            Document.status == DocumentStatus.REVIEW_PENDING,
        )
    ) or 0

    rejected_docs = await session.scalar(
        select(func.count(Document.id)).where(
            Document.project_id == project_id,
            Document.status == DocumentStatus.REJECTED,
        )
    ) or 0

    # LLM-Run Stats für Projekt-Dokumente
    llm_stats_query = await session.execute(
        select(
            func.avg(LlmRun.input_tokens).label("avg_in"),
            func.avg(LlmRun.output_tokens).label("avg_out"),
            func.avg(LlmRun.latency_ms).label("avg_latency"),
        )
        .join(Document, LlmRun.document_id == Document.id)
        .where(Document.project_id == project_id)
    )
    llm_stats = llm_stats_query.first()

    # RAG-Examples aus Projekt-Feedback
    rag_examples_used = await session.scalar(
        select(func.count(RagExample.id))
        .join(Feedback, RagExample.feedback_id == Feedback.id)
        .join(Document, Feedback.document_id == Document.id)
        .where(Document.project_id == project_id)
    ) or 0

    return {
        "project_id": project_id,
        "counters": {
            "documents_total": total_docs,
            "accepted": accepted_docs,
            "review_pending": review_pending,
            "rejected": rejected_docs,
            "rag_examples_used": rag_examples_used,
        },
        "timings": {
            "avg_parse_ms": 0,  # TODO: ParseRun hat kein aggregiertes Timing
            "avg_llm_ms": round(llm_stats.avg_latency or 0) if llm_stats else 0,
            "avg_total_ms": round(llm_stats.avg_latency or 0) if llm_stats else 0,
        },
        "tokens": {
            "avg_in": round(llm_stats.avg_in or 0) if llm_stats else 0,
            "avg_out": round(llm_stats.avg_out or 0) if llm_stats else 0,
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

    # Rating-Verteilung
    correct_count = await session.scalar(
        select(func.count(Feedback.id)).where(Feedback.rating == "CORRECT")
    ) or 0
    partial_count = await session.scalar(
        select(func.count(Feedback.id)).where(Feedback.rating == "PARTIAL")
    ) or 0
    wrong_count = await session.scalar(
        select(func.count(Feedback.id)).where(Feedback.rating.in_(["WRONG", "INCORRECT"]))
    ) or 0

    # Durchschnittliche Korrekturen pro Feedback
    feedbacks_with_corrections = await session.scalar(
        select(func.count(Feedback.id)).where(Feedback.corrections.isnot(None))
    ) or 0

    # RAG-Examples-Statistik
    total_rag_examples = await session.scalar(select(func.count(RagExample.id))) or 0

    return {
        "summary": {
            "total_feedback_entries": total_feedback,
            "rating_distribution": {
                "CORRECT": correct_count,
                "PARTIAL": partial_count,
                "WRONG": wrong_count,
            },
            "avg_corrections_per_analysis": (
                feedbacks_with_corrections / total_feedback if total_feedback > 0 else 0.0
            ),
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
            "examples_contributing": total_rag_examples,
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

    # Aggregierte LLM-Statistiken
    llm_agg_query = await session.execute(
        select(
            func.avg(LlmRun.input_tokens).label("avg_in"),
            func.avg(LlmRun.output_tokens).label("avg_out"),
            func.sum(LlmRun.input_tokens + LlmRun.output_tokens).label("total_tokens"),
            func.avg(LlmRun.latency_ms).label("avg_latency"),
            func.min(LlmRun.latency_ms).label("min_latency"),
            func.max(LlmRun.latency_ms).label("max_latency"),
        )
    )
    llm_agg = llm_agg_query.first()

    avg_tokens_in = round(llm_agg.avg_in or 0) if llm_agg else 0
    avg_tokens_out = round(llm_agg.avg_out or 0) if llm_agg else 0
    total_tokens = int(llm_agg.total_tokens or 0) if llm_agg else 0
    avg_latency = round(llm_agg.avg_latency or 0) if llm_agg else 0
    min_latency = int(llm_agg.min_latency or 0) if llm_agg else 0
    max_latency = int(llm_agg.max_latency or 0) if llm_agg else 0

    # Tokens pro Sekunde berechnen
    tokens_per_second = 0.0
    if avg_latency > 0 and avg_tokens_out > 0:
        tokens_per_second = round(avg_tokens_out / (avg_latency / 1000), 1)

    # Fehler-Statistiken (Status != COMPLETED)
    error_count = await session.scalar(
        select(func.count(LlmRun.id)).where(LlmRun.status != "COMPLETED")
    ) or 0

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
            "avg_tokens_in": avg_tokens_in,
            "avg_tokens_out": avg_tokens_out,
            "total_tokens_processed": total_tokens,
            "avg_inference_time_ms": avg_latency,
            "min_inference_time_ms": min_latency,
            "max_inference_time_ms": max_latency,
            "tokens_per_second_avg": tokens_per_second,
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
            "connection_error_count": error_count,
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

    # System-Info (cpu/memory für zukünftige Erweiterung)
    _cpu_percent = psutil.cpu_percent()  # noqa: F841
    _memory = psutil.virtual_memory()  # noqa: F841
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


@router.get("/stats/users/active", response_model=ActiveUsersResponse)
async def get_active_user_count(
    admin: CurrentAdmin,
    session: AsyncSession = Depends(get_async_session),
) -> ActiveUsersResponse:
    """
    Zählt aktuell aktive Benutzer (Admin-only).

    Aktiv = last_active_at innerhalb der letzten 10 Minuten.
    Gemäß Nutzerkonzept Abschnitt 4.5.

    Returns:
        Anzahl aktiver Benutzer und Zeitstempel.
    """
    # Zeitfenster: 10 Minuten (entspricht Inaktivitäts-Timeout)
    cutoff = datetime.now(UTC) - timedelta(minutes=10)

    count = await session.scalar(
        select(func.count(User.id)).where(
            User.last_active_at >= cutoff,
            User.is_active.is_(True),
        )
    ) or 0

    return ActiveUsersResponse(
        active_users=count,
        timestamp=datetime.now(UTC).isoformat(),
    )
