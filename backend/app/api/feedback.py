# Pfad: /backend/app/api/feedback.py
"""
FlowAudit Feedback API

Endpoints für Human-in-the-loop Feedback.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.document import Document
from app.models.enums import DocumentStatus
from app.models.feedback import Feedback
from app.models.result import FinalResult
from app.schemas.feedback import FeedbackCreate, FeedbackListItem, FeedbackResponse

router = APIRouter()


@router.post("/documents/{document_id}/feedback", status_code=status.HTTP_201_CREATED)
async def create_feedback(
    document_id: str,
    data: FeedbackCreate,
    session: AsyncSession = Depends(get_async_session),
) -> FeedbackResponse:
    """
    Erstellt Feedback zu Prüfergebnis.

    Args:
        document_id: Dokument-ID
        data: Feedback-Daten

    Returns:
        Erstelltes Feedback.
    """
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Feedback erstellen
    feedback = Feedback(
        document_id=document_id,
        final_result_id=data.final_result_id,
        rating=data.rating,
        comment=data.comment,
        overrides=[o.model_dump() for o in data.overrides],
        accept_result=data.accept_result,
    )

    session.add(feedback)

    # Dokument-Status aktualisieren
    if data.accept_result:
        document.status = DocumentStatus.ACCEPTED

    await session.flush()

    # TODO: RAG-Beispiel erstellen wenn Korrekturen vorhanden
    stored_rag_example_id = None

    return FeedbackResponse(
        id=feedback.id,
        document_id=feedback.document_id,
        final_result_id=feedback.final_result_id,
        rating=feedback.rating,
        comment=feedback.comment,
        overrides=data.overrides,
        accept_result=feedback.accept_result,
        stored_rag_example_id=stored_rag_example_id,
        document_status=document.status.value,
        created_at=feedback.created_at,
    )


@router.get("/documents/{document_id}/feedback")
async def list_feedback(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Listet Feedback für Dokument.

    Args:
        document_id: Dokument-ID

    Returns:
        Liste der Feedback-Einträge.
    """
    result = await session.execute(
        select(Feedback)
        .where(Feedback.document_id == document_id)
        .order_by(Feedback.created_at.desc())
    )
    feedback_list = result.scalars().all()

    data = [
        FeedbackListItem(
            feedback_id=f.id,
            rating=f.rating,
            override_count=len(f.overrides),
            created_at=f.created_at,
        )
        for f in feedback_list
    ]

    return {"data": [item.model_dump() for item in data]}


@router.post("/documents/{document_id}/finalize", status_code=status.HTTP_201_CREATED)
async def finalize_document(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Erstellt finales Ergebnis.

    Args:
        document_id: Dokument-ID

    Returns:
        Finales Ergebnis.
    """
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Final Result erstellen
    final_result = FinalResult(
        document_id=document_id,
        status="REVIEW_PENDING",
        fields=[],
        overall={
            "traffic_light": "YELLOW",
            "missing_required_features": [],
            "conflicts": [],
        },
    )

    session.add(final_result)
    document.status = DocumentStatus.REVIEW_PENDING
    await session.flush()

    return {
        "final_result_id": final_result.id,
        "document_id": document_id,
        "status": final_result.status,
        "computed": final_result.computed,
        "fields": final_result.fields,
        "overall": final_result.overall,
    }


@router.get("/final-results/{final_result_id}")
async def get_final_result(
    final_result_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Gibt finales Ergebnis zurück.

    Args:
        final_result_id: Ergebnis-ID

    Returns:
        Finales Ergebnis.
    """
    result = await session.execute(
        select(FinalResult).where(FinalResult.id == final_result_id)
    )
    final_result = result.scalar_one_or_none()

    if not final_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FinalResult {final_result_id} not found",
        )

    return {
        "final_result_id": final_result.id,
        "document_id": final_result.document_id,
        "llm_run_id": final_result.llm_run_id,
        "status": final_result.status,
        "computed": final_result.computed,
        "fields": final_result.fields,
        "overall": final_result.overall,
        "created_at": final_result.created_at.isoformat(),
        "updated_at": final_result.updated_at.isoformat() if final_result.updated_at else None,
    }


@router.get("/documents/{document_id}/final")
async def get_document_final_result(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Gibt neuestes finales Ergebnis für Dokument zurück.

    Args:
        document_id: Dokument-ID

    Returns:
        Finales Ergebnis.
    """
    result = await session.execute(
        select(FinalResult)
        .where(FinalResult.document_id == document_id)
        .order_by(FinalResult.created_at.desc())
        .limit(1)
    )
    final_result = result.scalar_one_or_none()

    if not final_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No final result for document {document_id}",
        )

    return {
        "final_result_id": final_result.id,
        "document_id": final_result.document_id,
        "status": final_result.status,
        "computed": final_result.computed,
        "fields": final_result.fields,
        "overall": final_result.overall,
    }
