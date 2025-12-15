# Pfad: /backend/app/api/rag.py
"""
FlowAudit RAG API

Endpoints für RAG-Beispiele und Retrieval.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.document import Document
from app.models.feedback import RagExample
from app.models.llm import LLMPayload
from app.rag import get_rag_service, get_vectorstore
from app.schemas.rag import (
    RagExampleListItem,
    RagExampleResponse,
    RagRetrieveMatch,
    RagRetrieveRequest,
    RagRetrieveResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class RagSearchRequest(BaseModel):
    """RAG-Such-Request."""

    query: str = Field(..., description="Suchtext")
    collection_type: str = Field(
        default="invoices", description="Collection (invoices, errors, patterns)"
    )
    n_results: int = Field(default=5, ge=1, le=20, description="Anzahl Ergebnisse")
    ruleset_id: str | None = Field(default=None, description="Filter nach Ruleset")


class RagSearchMatch(BaseModel):
    """RAG-Such-Treffer."""

    id: str
    score: float
    document: str
    metadata: dict[str, Any]


class RagSearchResponse(BaseModel):
    """RAG-Such-Response."""

    matches: list[RagSearchMatch]
    total: int


class RagStatsResponse(BaseModel):
    """RAG-Statistik-Response."""

    collections: dict[str, int]
    total_examples: int


@router.get("/rag/examples")
async def list_rag_examples(
    ruleset_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Listet RAG-Beispiele.

    Args:
        ruleset_id: Optional Filter nach Ruleset
        limit: Max. Anzahl
        offset: Offset

    Returns:
        Paginierte Liste der RAG-Beispiele.
    """
    query = select(RagExample)

    if ruleset_id:
        query = query.where(RagExample.ruleset_id == ruleset_id)

    # Total
    count_query = select(func.count(RagExample.id))
    if ruleset_id:
        count_query = count_query.where(RagExample.ruleset_id == ruleset_id)
    total = await session.scalar(count_query) or 0

    # Paginated
    query = query.order_by(RagExample.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    examples = result.scalars().all()

    data = [
        RagExampleListItem(
            rag_example_id=e.id,
            ruleset_id=e.ruleset_id,
            feature_id=e.feature_id,
            correction_type=e.correction_type,
            similarity_to_nearest=None,
            usage_count=e.usage_count,
            created_at=e.created_at,
        )
        for e in examples
    ]

    return {
        "data": [item.model_dump() for item in data],
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


@router.get("/rag/examples/{rag_example_id}")
async def get_rag_example(
    rag_example_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> RagExampleResponse:
    """
    Gibt RAG-Beispiel-Details zurück.

    Args:
        rag_example_id: Beispiel-ID

    Returns:
        RAG-Beispiel mit Inhalt.
    """
    result = await session.execute(
        select(RagExample).where(RagExample.id == rag_example_id)
    )
    example = result.scalar_one_or_none()

    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RagExample {rag_example_id} not found",
        )

    return RagExampleResponse(
        id=example.id,
        created_at=example.created_at,
        source={
            "document_id": example.document_id,
            "feedback_id": example.feedback_id,
            "project_id": example.project_id,
        },
        metadata={
            "ruleset_id": example.ruleset_id,
            "feature_id": example.feature_id,
            "correction_type": example.correction_type,
        },
        content={
            "original_text_snippet": example.original_text_snippet,
            "original_llm_result": example.original_llm_result,
            "corrected_result": example.corrected_result,
        },
        embedding_info={
            "text_embedded": example.embedding_text,
            "embedding_preview": None,
            "nearest_neighbors": None,
        },
        usage_stats={
            "times_retrieved": example.usage_count,
            "times_helpful": 0,
            "last_used": example.last_used_at,
        },
    )


@router.post("/rag/retrieve")
async def retrieve_rag_examples(
    data: RagRetrieveRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RagRetrieveResponse:
    """
    Retrieves ähnliche RAG-Beispiele basierend auf Payload.

    Args:
        data: Payload-ID und Top-K

    Returns:
        Ähnlichste Beispiele.
    """
    # Payload aus Datenbank laden
    result = await session.execute(
        select(LLMPayload).where(LLMPayload.id == data.payload_id)
    )
    payload = result.scalar_one_or_none()

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payload {data.payload_id} not found",
        )

    # VectorStore für Retrieval verwenden
    vectorstore = get_vectorstore()

    # Suchtext aus Payload extrahieren
    search_text = ""
    if payload.extracted_text:
        search_text = payload.extracted_text[:2000]
    elif payload.features:
        # Features zu Text zusammenfügen
        feature_texts = []
        for feature in payload.features:
            if isinstance(feature, dict):
                feature_texts.append(f"{feature.get('name', '')}: {feature.get('value', '')}")
        search_text = "\n".join(feature_texts)

    if not search_text:
        return RagRetrieveResponse(matches=[])

    # Ähnliche Rechnungen suchen
    search_results = vectorstore.find_similar_invoices(
        raw_text=search_text,
        extracted_data={},
        n_results=data.top_k,
        ruleset_id=payload.ruleset_id,
    )

    # Matches erstellen und Usage in DB aktualisieren
    matches: list[RagRetrieveMatch] = []
    for sr in search_results:
        matches.append(
            RagRetrieveMatch(
                rag_example_id=sr.id,
                similarity=sr.score,
                reason=f"Ähnlichkeit basierend auf Textinhalt (Score: {sr.score:.2f})",
            )
        )

        # Usage-Count in DB erhöhen, falls RAG-Example existiert
        rag_result = await session.execute(
            select(RagExample).where(RagExample.id == sr.id)
        )
        rag_example = rag_result.scalar_one_or_none()
        if rag_example:
            rag_example.usage_count += 1
            rag_example.last_used_at = datetime.now(timezone.utc)

    await session.commit()

    return RagRetrieveResponse(matches=matches)


@router.post("/rag/search")
async def search_rag(data: RagSearchRequest) -> RagSearchResponse:
    """
    Durchsucht RAG-Collections.

    Args:
        data: Suchparameter

    Returns:
        Suchergebnisse.
    """
    vectorstore = get_vectorstore()

    matches: list[RagSearchMatch] = []

    if data.collection_type == "invoices":
        results = vectorstore.find_similar_invoices(
            raw_text=data.query,
            extracted_data={},
            n_results=data.n_results,
            ruleset_id=data.ruleset_id,
        )
    elif data.collection_type == "errors":
        results = vectorstore.find_similar_errors(
            error_type="",
            feature_id="",
            context_text=data.query,
            n_results=data.n_results,
        )
    elif data.collection_type == "patterns":
        results = vectorstore.find_matching_patterns(
            text=data.query,
            n_results=data.n_results,
        )
    else:
        results = []

    for r in results:
        matches.append(
            RagSearchMatch(
                id=r.id,
                score=r.score,
                document=r.document,
                metadata=r.metadata,
            )
        )

    return RagSearchResponse(matches=matches, total=len(matches))


@router.get("/rag/stats")
async def get_rag_stats() -> RagStatsResponse:
    """
    Gibt RAG-Statistiken zurück.

    Returns:
        Collection-Statistiken.
    """
    rag_service = get_rag_service()
    stats = rag_service.get_stats()

    total = sum(stats.get("collections", {}).values())

    return RagStatsResponse(
        collections=stats.get("collections", {}),
        total_examples=total,
    )


@router.delete("/rag/examples/{rag_example_id}")
async def delete_rag_example(
    rag_example_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """
    Löscht RAG-Beispiel.

    Args:
        rag_example_id: Beispiel-ID

    Returns:
        Bestätigung.
    """
    result = await session.execute(
        select(RagExample).where(RagExample.id == rag_example_id)
    )
    example = result.scalar_one_or_none()

    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RagExample {rag_example_id} not found",
        )

    await session.delete(example)
    await session.commit()

    logger.info(f"Deleted RAG example: {rag_example_id}")

    return {"status": "deleted", "rag_example_id": rag_example_id}
