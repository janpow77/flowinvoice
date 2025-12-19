# Pfad: /backend/app/api/feedback.py
"""
FlowAudit Feedback API

Endpoints für Human-in-the-loop Feedback.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.document import Document, ParseRun
from app.models.document_type import DocumentTypeSettings
from app.models.enums import DocumentStatus
from app.models.feedback import Feedback, RagExample
from app.models.llm import LlmRun
from app.models.result import FinalResult
from app.rag import get_rag_service, get_vectorstore
from app.schemas.feedback import FeedbackCreate, FeedbackListItem, FeedbackResponse
from app.services.parser import ParseResult, ExtractedValue

logger = logging.getLogger(__name__)

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

    # RAG-Beispiel erstellen wenn Korrekturen vorhanden
    stored_rag_example_id = None

    if data.overrides and len(data.overrides) > 0:
        try:
            # Parse-Run für Originaltext laden
            parse_run_result = await session.execute(
                select(ParseRun)
                .where(ParseRun.document_id == document_id)
                .order_by(ParseRun.created_at.desc())
                .limit(1)
            )
            parse_run = parse_run_result.scalar_one_or_none()

            # LLM-Run für Original-Ergebnis laden (für zukünftige Nutzung)
            llm_run_result = await session.execute(
                select(LlmRun)
                .where(LlmRun.document_id == document_id)
                .order_by(LlmRun.created_at.desc())
                .limit(1)
            )
            _llm_run = llm_run_result.scalar_one_or_none()  # noqa: F841

            # Für jede Korrektur ein RAG-Beispiel erstellen
            for override in data.overrides:
                # Embedding-Text zusammenstellen
                embedding_parts = []
                if parse_run and parse_run.raw_text:
                    # Ersten 500 Zeichen des Originaltexts
                    embedding_parts.append(parse_run.raw_text[:500])
                embedding_parts.append(f"Feature: {override.feature_id}")
                embedding_parts.append(f"Original: {override.original_value}")
                embedding_parts.append(f"Korrigiert: {override.corrected_value}")
                if override.reason:
                    embedding_parts.append(f"Grund: {override.reason}")

                embedding_text = "\n".join(embedding_parts)

                # RAG-Beispiel in DB erstellen
                rag_example = RagExample(
                    document_id=document_id,
                    feedback_id=feedback.id,
                    project_id=document.project_id,
                    ruleset_id=document.ruleset_id or "DE_USTG",
                    feature_id=override.feature_id,
                    correction_type=override.correction_type or "manual_correction",
                    original_text_snippet=parse_run.raw_text[:1000] if parse_run and parse_run.raw_text else None,
                    original_llm_result={
                        "feature_id": override.feature_id,
                        "value": override.original_value,
                    } if override.original_value else None,
                    corrected_result={
                        "feature_id": override.feature_id,
                        "value": override.corrected_value,
                        "reason": override.reason,
                    },
                    embedding_text=embedding_text,
                )
                session.add(rag_example)
                await session.flush()

                # In ChromaDB speichern
                try:
                    vectorstore = get_vectorstore()
                    vectorstore.add_error_example(
                        error_id=rag_example.id,
                        error_type=override.correction_type or "manual_correction",
                        feature_id=override.feature_id,
                        context_text=parse_run.raw_text[:500] if parse_run and parse_run.raw_text else "",
                        wrong_value=str(override.original_value) if override.original_value else "",
                        correct_value=str(override.corrected_value) if override.corrected_value else "",
                        reasoning=override.reason or "Manuelle Korrektur durch Benutzer",
                        ruleset_id=document.ruleset_id or "DE_USTG",
                    )
                except Exception as e:
                    logger.warning(f"Failed to store RAG example in ChromaDB: {e}")

                # Erste ID für Response speichern
                if stored_rag_example_id is None:
                    stored_rag_example_id = rag_example.id

            logger.info(f"Created {len(data.overrides)} RAG examples from feedback {feedback.id}")

        except Exception as e:
            logger.exception(f"Error creating RAG examples: {e}")
            # Fehler bei RAG-Erstellung sollte Feedback nicht verhindern

    # Bei Akzeptierung: Vollständiges Dokument für RAG lernen (mit Chunking)
    if data.accept_result:
        try:
            # Raw-Text aus Dokument holen (bevorzugt) oder aus ParseRun
            raw_text = document.raw_text
            extracted_data_source = document.extracted_data

            if not raw_text:
                # Fallback: Parse-Run für Rohtext laden
                parse_run_result = await session.execute(
                    select(ParseRun)
                    .where(ParseRun.document_id == document_id)
                    .order_by(ParseRun.created_at.desc())
                    .limit(1)
                )
                parse_run = parse_run_result.scalar_one_or_none()
                if parse_run:
                    raw_text = parse_run.raw_text
                    extracted_data_source = parse_run.extracted_data

            if raw_text:
                # Dokumenttyp-Einstellungen laden für Chunking-Config
                doc_type_slug = document.document_type.value.lower()
                doc_type_result = await session.execute(
                    select(DocumentTypeSettings).where(
                        DocumentTypeSettings.slug == doc_type_slug
                    )
                )
                doc_type_settings = doc_type_result.scalar_one_or_none()

                # Chunking-Config erstellen
                chunking_config = None
                if doc_type_settings:
                    chunking_config = {
                        "chunk_size_tokens": doc_type_settings.chunk_size_tokens,
                        "chunk_overlap_tokens": doc_type_settings.chunk_overlap_tokens,
                        "max_chunks": doc_type_settings.max_chunks,
                        "strategy": doc_type_settings.chunk_strategy,
                    }
                    logger.info(
                        f"Using chunking config for {doc_type_slug}: "
                        f"size={doc_type_settings.chunk_size_tokens}, "
                        f"overlap={doc_type_settings.chunk_overlap_tokens}, "
                        f"max={doc_type_settings.max_chunks}"
                    )

                # ParseResult rekonstruieren
                extracted_data = {}
                if extracted_data_source:
                    for key, value in extracted_data_source.items():
                        if isinstance(value, dict):
                            extracted_data[key] = ExtractedValue(
                                value=value.get("value"),
                                raw_text=str(value.get("raw_text", value.get("value", ""))),
                                confidence=value.get("confidence", 0.0),
                                source=value.get("source", "unknown"),
                            )
                        else:
                            extracted_data[key] = ExtractedValue(
                                value=value,
                                raw_text=str(value) if value else "",
                                confidence=1.0,
                                source="parse_run",
                            )

                parse_result = ParseResult(
                    raw_text=raw_text,
                    pages=[],  # Seiten nicht mehr verfügbar nach Parse
                    extracted=extracted_data,
                    timings_ms={},
                )

                # Korrekturen für RAG vorbereiten
                corrections = None
                if data.overrides:
                    corrections = [
                        {
                            "error_type": o.correction_type or "manual_correction",
                            "feature_id": o.feature_id,
                            "wrong_value": str(o.original_value) if o.original_value else "",
                            "correct_value": str(o.corrected_value) if o.corrected_value else "",
                            "reasoning": o.reason or "",
                        }
                        for o in data.overrides
                    ]

                # RAG Service: Validierte Rechnung lernen
                rag_service = get_rag_service()
                rag_service.learn_from_validation(
                    document_id=document_id,
                    parse_result=parse_result,
                    final_assessment="accepted",
                    corrections=corrections,
                    ruleset_id=document.ruleset_id or "DE_USTG",
                    chunking_config=chunking_config,
                )

                logger.info(
                    f"Learned from validated document {document_id} "
                    f"(chunking: {chunking_config is not None})"
                )

        except Exception as e:
            logger.exception(f"Error learning from validation: {e}")
            # Fehler sollte Feedback nicht verhindern

    await session.commit()

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
