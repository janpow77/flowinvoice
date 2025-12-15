# Pfad: /backend/app/api/rag.py
"""
FlowAudit RAG API

Endpoints für RAG-Beispiele und Retrieval.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.feedback import RagExample
from app.schemas.rag import (
    RagExampleListItem,
    RagExampleResponse,
    RagRetrieveRequest,
    RagRetrieveResponse,
)

router = APIRouter()


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
    Retrieves ähnliche RAG-Beispiele (Debug).

    Args:
        data: Payload-ID und Top-K

    Returns:
        Ähnlichste Beispiele.
    """
    # TODO: Echte ChromaDB-Retrieval-Integration
    # Placeholder-Antwort
    return RagRetrieveResponse(matches=[])
