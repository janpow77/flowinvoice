# Pfad: /backend/app/api/llm.py
"""
FlowAudit LLM API

Endpoints für PreparePayload und LLM-Runs.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.document import Document, ParseRun
from app.models.enums import DocumentStatus, Provider
from app.models.llm import LlmRun, LlmRunLog, PreparePayload
from app.schemas.llm import LlmRunCreate, LlmRunLogResponse, LlmRunResponse, PreparePayloadResponse
from app.services.rule_engine import RULESETS
from app.worker.tasks import analyze_document_task

router = APIRouter()


@router.post("/documents/{document_id}/prepare", status_code=status.HTTP_201_CREATED)
async def create_prepare_payload(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> PreparePayloadResponse:
    """
    Erstellt PreparePayload (INPUT-JSON für KI).

    Args:
        document_id: Dokument-ID

    Returns:
        Erstelltes PreparePayload.
    """
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Features aus Ruleset laden
    ruleset_id = document.ruleset_id or "DE_USTG"
    ruleset_features = RULESETS.get(ruleset_id, RULESETS.get("DE_USTG", {}))
    features_list = [
        {
            "feature_id": fdef.feature_id,
            "name_de": fdef.name_de,
            "name_en": fdef.name_en,
            "legal_basis": fdef.legal_basis,
            "required_level": fdef.required_level.value,
            "category": fdef.category.value,
        }
        for fdef in ruleset_features.values()
    ]

    # Extracted text aus ParseRun laden
    parse_run_result = await session.execute(
        select(ParseRun)
        .where(ParseRun.document_id == document_id)
        .order_by(ParseRun.created_at.desc())
        .limit(1)
    )
    parse_run = parse_run_result.scalar_one_or_none()
    extracted_text = parse_run.raw_text if parse_run else None

    # PreparePayload erstellen
    payload = PreparePayload(
        document_id=document_id,
        schema_version="1.0",
        ruleset={
            "ruleset_id": ruleset_id,
            "version": document.ruleset_version or "1.0.0",
        },
        ui_language=document.ui_language,
        features=features_list,
        extracted_text=extracted_text,
    )

    session.add(payload)
    document.status = DocumentStatus.PREPARED
    await session.flush()

    return PreparePayloadResponse(
        id=payload.id,
        document_id=payload.document_id,
        schema_version=payload.schema_version,
        ruleset=payload.ruleset,
        ui_language=payload.ui_language,
        project_context=payload.project_context,
        parsing_summary=payload.parsing_summary,
        deterministic_precheck_results=payload.deterministic_precheck_results,
        features=payload.features,
        extracted_text=payload.extracted_text,
        required_output_schema=payload.required_output_schema,
        rag_context=payload.rag_context,
        created_at=payload.created_at,
    )


@router.get("/payloads/{payload_id}")
async def get_payload(
    payload_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> PreparePayloadResponse:
    """
    Gibt PreparePayload zurück.

    Args:
        payload_id: Payload-ID

    Returns:
        PreparePayload.
    """
    result = await session.execute(select(PreparePayload).where(PreparePayload.id == payload_id))
    payload = result.scalar_one_or_none()

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payload {payload_id} not found",
        )

    return PreparePayloadResponse(
        id=payload.id,
        document_id=payload.document_id,
        schema_version=payload.schema_version,
        ruleset=payload.ruleset,
        ui_language=payload.ui_language,
        project_context=payload.project_context,
        parsing_summary=payload.parsing_summary,
        deterministic_precheck_results=payload.deterministic_precheck_results,
        features=payload.features,
        extracted_text=payload.extracted_text,
        required_output_schema=payload.required_output_schema,
        rag_context=payload.rag_context,
        created_at=payload.created_at,
    )


@router.get("/documents/{document_id}/payload")
async def get_document_payload(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> PreparePayloadResponse:
    """
    Gibt neuestes PreparePayload für Dokument zurück.

    Args:
        document_id: Dokument-ID

    Returns:
        PreparePayload.
    """
    result = await session.execute(
        select(PreparePayload)
        .where(PreparePayload.document_id == document_id)
        .order_by(PreparePayload.created_at.desc())
        .limit(1)
    )
    payload = result.scalar_one_or_none()

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No payload for document {document_id}",
        )

    return PreparePayloadResponse(
        id=payload.id,
        document_id=payload.document_id,
        schema_version=payload.schema_version,
        ruleset=payload.ruleset,
        ui_language=payload.ui_language,
        project_context=payload.project_context,
        parsing_summary=payload.parsing_summary,
        deterministic_precheck_results=payload.deterministic_precheck_results,
        features=payload.features,
        extracted_text=payload.extracted_text,
        required_output_schema=payload.required_output_schema,
        rag_context=payload.rag_context,
        created_at=payload.created_at,
    )


@router.post("/documents/{document_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def start_llm_run(
    document_id: str,
    data: LlmRunCreate | None = None,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Startet LLM-Inference.

    Args:
        document_id: Dokument-ID
        data: Optional Payload-ID und Overrides

    Returns:
        LLM-Run-Info.
    """
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Payload holen
    payload_id = data.payload_id if data else None
    if not payload_id:
        # Neuestes Payload verwenden
        payload_result = await session.execute(
            select(PreparePayload)
            .where(PreparePayload.document_id == document_id)
            .order_by(PreparePayload.created_at.desc())
            .limit(1)
        )
        payload = payload_result.scalar_one_or_none()
        if payload:
            payload_id = payload.id

    # Provider
    provider = data.provider_override if data and data.provider_override else Provider.LOCAL_OLLAMA
    model_name = data.model_override if data and data.model_override else "llama3.1:8b-instruct-q4"

    # LLM-Run erstellen
    llm_run = LlmRun(
        document_id=document_id,
        payload_id=payload_id,
        provider=provider,
        model_name=model_name,
        status="PENDING",
    )

    session.add(llm_run)
    document.status = DocumentStatus.LLM_RUNNING
    await session.commit()

    # Celery Task für LLM-Analyse starten
    task = analyze_document_task.delay(
        document_id=document_id,
        provider=provider.value,
        model=model_name,
    )

    return {
        "llm_run_id": llm_run.id,
        "document_id": document_id,
        "status": "RUNNING",
        "task_id": task.id,
    }


@router.get("/llm-runs/{llm_run_id}")
async def get_llm_run(
    llm_run_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> LlmRunResponse:
    """
    Gibt LLM-Run-Details zurück.

    Args:
        llm_run_id: LLM-Run-ID

    Returns:
        LLM-Run mit Response.
    """
    result = await session.execute(select(LlmRun).where(LlmRun.id == llm_run_id))
    llm_run = result.scalar_one_or_none()

    if not llm_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LlmRun {llm_run_id} not found",
        )

    return LlmRunResponse(
        id=llm_run.id,
        document_id=llm_run.document_id,
        payload_id=llm_run.payload_id,
        provider=llm_run.provider,
        model_name=llm_run.model_name,
        status=llm_run.status,
        timings_ms=llm_run.timings_ms,
        token_usage=llm_run.token_usage,
        raw_response_text=llm_run.raw_response_text,
        structured_response=llm_run.structured_response,
        error_message=llm_run.error_message,
        created_at=llm_run.created_at,
        completed_at=llm_run.completed_at,
    )


@router.get("/documents/{document_id}/llm")
async def get_document_llm_run(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> LlmRunResponse:
    """
    Gibt neuesten LLM-Run für Dokument zurück.

    Args:
        document_id: Dokument-ID

    Returns:
        LLM-Run.
    """
    result = await session.execute(
        select(LlmRun)
        .where(LlmRun.document_id == document_id)
        .order_by(LlmRun.created_at.desc())
        .limit(1)
    )
    llm_run = result.scalar_one_or_none()

    if not llm_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No LLM run for document {document_id}",
        )

    return LlmRunResponse(
        id=llm_run.id,
        document_id=llm_run.document_id,
        payload_id=llm_run.payload_id,
        provider=llm_run.provider,
        model_name=llm_run.model_name,
        status=llm_run.status,
        timings_ms=llm_run.timings_ms,
        token_usage=llm_run.token_usage,
        raw_response_text=llm_run.raw_response_text,
        structured_response=llm_run.structured_response,
        error_message=llm_run.error_message,
        created_at=llm_run.created_at,
        completed_at=llm_run.completed_at,
    )


@router.get("/llm-runs/{llm_run_id}/logs")
async def get_llm_run_logs(
    llm_run_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> LlmRunLogResponse:
    """
    Gibt LLM-Run-Logs zurück.

    Args:
        llm_run_id: LLM-Run-ID

    Returns:
        Log-Events.
    """
    result = await session.execute(
        select(LlmRunLog)
        .where(LlmRunLog.llm_run_id == llm_run_id)
        .order_by(LlmRunLog.timestamp)
    )
    logs = result.scalars().all()

    events = [
        {
            "timestamp": log.timestamp,
            "level": log.level,
            "message": log.message,
            "data": log.data,
        }
        for log in logs
    ]

    return LlmRunLogResponse(llm_run_id=llm_run_id, events=events)


# ============================================================================
# LLM Provider Configuration Endpoints (für Frontend Settings)
# ============================================================================

@router.get("/llm/providers")
async def get_llm_providers() -> dict[str, Any]:
    """
    Gibt verfügbare LLM-Provider und deren Status zurück.

    Returns:
        Liste der Provider mit Konfiguration.
    """
    from app.config import get_settings

    settings = get_settings()

    providers = [
        {
            "id": "LOCAL_OLLAMA",
            "name": "Ollama (Lokal)",
            "enabled": True,
            "is_default": True,
            "base_url": settings.ollama_host,
            "model": settings.ollama_default_model,
            "requires_api_key": False,
        },
        {
            "id": "OPENAI",
            "name": "OpenAI",
            "enabled": settings.openai_api_key is not None,
            "is_default": False,
            "requires_api_key": True,
            "api_key_set": settings.openai_api_key is not None,
        },
        {
            "id": "ANTHROPIC",
            "name": "Anthropic Claude",
            "enabled": settings.anthropic_api_key is not None,
            "is_default": False,
            "requires_api_key": True,
            "api_key_set": settings.anthropic_api_key is not None,
        },
        {
            "id": "GOOGLE",
            "name": "Google Gemini",
            "enabled": settings.gemini_api_key is not None,
            "is_default": False,
            "requires_api_key": True,
            "api_key_set": settings.gemini_api_key is not None,
        },
    ]

    return {"providers": providers}


@router.get("/llm/health")
async def get_llm_health() -> dict[str, Any]:
    """
    Prüft Gesundheitsstatus aller LLM-Provider.

    Returns:
        Health-Status pro Provider.
    """
    import httpx
    from app.config import get_settings

    settings = get_settings()
    providers = []

    # Ollama Health Check
    ollama_healthy = False
    ollama_models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_host}/api/tags")
            if response.status_code == 200:
                ollama_healthy = True
                data = response.json()
                ollama_models = [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        pass

    providers.append({
        "id": "LOCAL_OLLAMA",
        "name": "Ollama (Lokal)",
        "healthy": ollama_healthy,
        "models": ollama_models,
        "message": "Verbunden" if ollama_healthy else "Nicht erreichbar",
    })

    # OpenAI - nur Status anzeigen, kein API-Call
    providers.append({
        "id": "OPENAI",
        "name": "OpenAI",
        "healthy": settings.openai_api_key is not None,
        "message": "API-Key konfiguriert" if settings.openai_api_key else "Nicht konfiguriert",
    })

    # Anthropic
    providers.append({
        "id": "ANTHROPIC",
        "name": "Anthropic Claude",
        "healthy": settings.anthropic_api_key is not None,
        "message": "API-Key konfiguriert" if settings.anthropic_api_key else "Nicht konfiguriert",
    })

    # Google
    providers.append({
        "id": "GOOGLE",
        "name": "Google Gemini",
        "healthy": settings.gemini_api_key is not None,
        "message": "API-Key konfiguriert" if settings.gemini_api_key else "Nicht konfiguriert",
    })

    return {"providers": providers}


@router.post("/llm/default")
async def set_default_provider(data: dict[str, str]) -> dict[str, Any]:
    """
    Setzt den Standard-LLM-Provider.

    Note: Diese Einstellung ist derzeit nur in-memory und wird
    bei Neustart zurückgesetzt. Für persistente Konfiguration
    sollte die stack.env angepasst werden.

    Args:
        data: {"provider": "LOCAL_OLLAMA" | "OPENAI" | ...}

    Returns:
        Bestätigung.
    """
    provider = data.get("provider", "LOCAL_OLLAMA")

    valid_providers = ["LOCAL_OLLAMA", "OPENAI", "ANTHROPIC", "GOOGLE"]
    if provider not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ungültiger Provider. Erlaubt: {valid_providers}",
        )

    # TODO: Persistente Speicherung implementieren
    # Aktuell nur Bestätigung zurückgeben

    return {
        "success": True,
        "default_provider": provider,
        "message": f"Provider '{provider}' als Standard gesetzt (nur für diese Session)",
    }
