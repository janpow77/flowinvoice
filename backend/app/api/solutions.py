# Pfad: /backend/app/api/solutions.py
"""
FlowAudit Solution File API

Endpoints für Lösungsdatei-Import und -Verarbeitung.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.document import Document
from app.models.enums import MatchingStrategy, SolutionFileFormat
from app.models.project import Project
from app.models.solution import SolutionFile, SolutionMatch
from app.schemas.solution import (
    ApplyOptionsSchema,
    AppliedCorrectionSchema,
    MatchPreviewItem,
    SolutionApplyResponse,
    SolutionFileListItem,
    SolutionFileUploadResponse,
    SolutionPreviewResponse,
)
from app.rag.vectorstore import get_vectorstore
from app.services.solution_matcher import DocumentInfo, SolutionMatcher
from app.services.solution_parser import SolutionFileParser

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/projects/{project_id}/solutions/upload",
    response_model=SolutionFileUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_solution_file(
    project_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
) -> SolutionFileUploadResponse:
    """
    Lädt eine Lösungsdatei für ein Projekt hoch.

    Unterstützte Formate:
    - JSON: Objekt mit "invoices" Array
    - JSONL: Eine JSON-Zeile pro Rechnung
    - CSV: Spaltenbasiertes Format

    Args:
        project_id: Projekt-ID
        file: Lösungsdatei

    Returns:
        Upload-Ergebnis mit Statistiken
    """
    # Projekt prüfen
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projekt {project_id} nicht gefunden",
        )

    # Datei lesen
    content = await file.read()
    try:
        content_str = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content_str = content.decode("latin-1")
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datei konnte nicht dekodiert werden (UTF-8/Latin-1)",
            ) from e

    # Parsen
    parser = SolutionFileParser()
    try:
        parsed = parser.parse(content_str, file.filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fehler beim Parsen: {e}",
        ) from e

    # In DB speichern
    solution_file = SolutionFile(
        project_id=project_id,
        filename=file.filename or "solution.json",
        format=parsed.format.value,
        file_size=len(content),
        generator_version=parsed.generator_version,
        generated_at=parsed.generated_at,
        entry_count=parsed.total_count,
        valid_count=parsed.valid_count,
        invalid_count=parsed.invalid_count,
        error_count=parsed.error_count,
        entries=[e.to_dict() for e in parsed.entries],
    )
    session.add(solution_file)
    await session.commit()

    logger.info(
        f"Lösungsdatei hochgeladen: {file.filename} mit {parsed.total_count} Einträgen"
    )

    return SolutionFileUploadResponse(
        solution_file_id=solution_file.id,
        format=parsed.format,
        entry_count=parsed.total_count,
        valid_count=parsed.valid_count,
        invalid_count=parsed.invalid_count,
        error_count=parsed.error_count,
        generator_version=parsed.generator_version,
    )


@router.get(
    "/projects/{project_id}/solutions",
    response_model=list[SolutionFileListItem],
)
async def list_solution_files(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> list[SolutionFileListItem]:
    """
    Listet alle Lösungsdateien für ein Projekt.

    Args:
        project_id: Projekt-ID

    Returns:
        Liste der Lösungsdateien
    """
    result = await session.execute(
        select(SolutionFile)
        .where(SolutionFile.project_id == project_id)
        .order_by(SolutionFile.created_at.desc())
    )
    files = result.scalars().all()

    return [
        SolutionFileListItem(
            id=f.id,
            project_id=f.project_id,
            filename=f.filename,
            format=SolutionFileFormat(f.format),
            entry_count=f.entry_count,
            applied=f.applied,
            applied_at=f.applied_at,
            created_at=f.created_at,
        )
        for f in files
    ]


@router.post(
    "/projects/{project_id}/solutions/{solution_file_id}/preview",
    response_model=SolutionPreviewResponse,
)
async def preview_solution_matching(
    project_id: str,
    solution_file_id: str,
    strategy: MatchingStrategy = Query(
        default=MatchingStrategy.FILENAME_POSITION,
        description="Matching-Strategie",
    ),
    session: AsyncSession = Depends(get_async_session),
) -> SolutionPreviewResponse:
    """
    Vorschau der Zuordnung von Lösungsdatei zu Dokumenten.

    Args:
        project_id: Projekt-ID
        solution_file_id: Lösungsdatei-ID
        strategy: Matching-Strategie

    Returns:
        Vorschau der Zuordnungen
    """
    # Lösungsdatei laden
    result = await session.execute(
        select(SolutionFile).where(
            SolutionFile.id == solution_file_id,
            SolutionFile.project_id == project_id,
        )
    )
    solution_file = result.scalar_one_or_none()
    if not solution_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lösungsdatei nicht gefunden",
        )

    # Dokumente des Projekts laden
    doc_result = await session.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at)
    )
    documents = doc_result.scalars().all()

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keine Dokumente im Projekt vorhanden",
        )

    # DocumentInfo erstellen
    doc_infos = [
        DocumentInfo(
            document_id=doc.id,
            filename=doc.filename,
            upload_position=idx + 1,
            upload_time=doc.created_at,
        )
        for idx, doc in enumerate(documents)
    ]

    # Lösungsdatei rekonstruieren
    from app.services.solution_parser import ParsedSolutionFile, SolutionEntry

    entries = [SolutionEntry.from_dict(e) for e in solution_file.entries]
    parsed = ParsedSolutionFile(
        format=SolutionFileFormat(solution_file.format),
        entries=entries,
        generator_version=solution_file.generator_version,
    )

    # Matching durchführen
    matcher = SolutionMatcher(strategy=strategy)
    matching_result = matcher.match(doc_infos, parsed, strategy)

    # Warnungen sammeln
    warnings: list[str] = []
    if matching_result.unmatched_documents:
        warnings.append(
            f"{len(matching_result.unmatched_documents)} Dokumente ohne Zuordnung"
        )
    if matching_result.unmatched_solutions:
        warnings.append(
            f"{len(matching_result.unmatched_solutions)} Lösungen ohne Dokument"
        )

    low_confidence = [m for m in matching_result.matched if m.match_confidence < 0.8]
    if low_confidence:
        warnings.append(f"{len(low_confidence)} Zuordnungen mit niedriger Konfidenz")

    return SolutionPreviewResponse(
        solution_file_id=solution_file_id,
        project_id=project_id,
        strategy=strategy,
        matched_count=matching_result.match_count,
        unmatched_documents=len(matching_result.unmatched_documents),
        unmatched_solutions=len(matching_result.unmatched_solutions),
        match_rate=matching_result.match_rate,
        matches=[
            MatchPreviewItem(
                document_id=m.document_id,
                document_filename=m.document_filename,
                solution_filename=m.solution_entry.filename,
                solution_position=m.solution_entry.position,
                is_valid=m.solution_entry.is_valid,
                error_count=len(m.solution_entry.errors),
                error_codes=m.solution_entry.error_codes,
                confidence=m.match_confidence,
                match_reason=m.match_reason,
            )
            for m in matching_result.matched
        ],
        warnings=warnings,
    )


@router.post(
    "/projects/{project_id}/solutions/{solution_file_id}/apply",
    response_model=SolutionApplyResponse,
)
async def apply_solution_file(
    project_id: str,
    solution_file_id: str,
    options: ApplyOptionsSchema | None = None,
    session: AsyncSession = Depends(get_async_session),
) -> SolutionApplyResponse:
    """
    Wendet eine Lösungsdatei auf die Dokumente an.

    Erstellt Feedback-Einträge und optional RAG-Beispiele.

    Args:
        project_id: Projekt-ID
        solution_file_id: Lösungsdatei-ID
        options: Anwendungsoptionen

    Returns:
        Anwendungsergebnis
    """
    if options is None:
        options = ApplyOptionsSchema()

    # Lösungsdatei laden
    result = await session.execute(
        select(SolutionFile).where(
            SolutionFile.id == solution_file_id,
            SolutionFile.project_id == project_id,
        )
    )
    solution_file = result.scalar_one_or_none()
    if not solution_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lösungsdatei nicht gefunden",
        )

    if solution_file.applied and not options.overwrite_existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lösungsdatei wurde bereits angewendet. "
            "Setze overwrite_existing=true zum Überschreiben.",
        )

    # Dokumente laden
    doc_result = await session.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at)
    )
    documents = doc_result.scalars().all()

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keine Dokumente im Projekt vorhanden",
        )

    # DocumentInfo erstellen
    doc_infos = [
        DocumentInfo(
            document_id=doc.id,
            filename=doc.filename,
            upload_position=idx + 1,
            upload_time=doc.created_at,
        )
        for idx, doc in enumerate(documents)
    ]

    # Lösungsdatei rekonstruieren
    from app.services.solution_parser import ParsedSolutionFile, SolutionEntry

    entries = [SolutionEntry.from_dict(e) for e in solution_file.entries]
    parsed = ParsedSolutionFile(
        format=SolutionFileFormat(solution_file.format),
        entries=entries,
        generator_version=solution_file.generator_version,
    )

    # Matching durchführen
    matcher = SolutionMatcher(strategy=options.strategy)
    matching_result = matcher.match(doc_infos, parsed, options.strategy)

    # Anwenden
    corrections: list[AppliedCorrectionSchema] = []
    applied_count = 0
    skipped_count = 0
    total_rag_examples = 0
    errors: list[str] = []

    for match in matching_result.matched:
        # Konfidenz prüfen
        if match.match_confidence < options.min_confidence:
            skipped_count += 1
            continue

        try:
            # SolutionMatch erstellen
            solution_match = SolutionMatch(
                solution_file_id=solution_file_id,
                document_id=match.document_id,
                solution_position=match.solution_entry.position,
                solution_filename=match.solution_entry.filename,
                match_confidence=match.match_confidence,
                match_reason=match.match_reason,
                strategy_used=match.strategy_used.value,
                is_valid=match.solution_entry.is_valid,
                errors=[e.to_dict() for e in match.solution_entry.errors],
                fields=match.solution_entry.fields,
                applied=True,
                applied_at=datetime.utcnow(),
                errors_applied=len(match.solution_entry.errors),
                fields_updated=len(match.solution_entry.fields),
            )
            session.add(solution_match)

            # RAG-Beispiele erstellen (wenn aktiviert und Fehler vorhanden)
            rag_created = 0
            if options.create_rag_examples and match.solution_entry.errors:
                try:
                    vectorstore = get_vectorstore()
                    # Dokument für raw_text laden
                    doc_result = await session.execute(
                        select(Document).where(Document.id == match.document_id)
                    )
                    doc = doc_result.scalar_one_or_none()
                    raw_text = ""
                    if doc and doc.parse_runs:
                        # Letzten erfolgreichen Parse-Run nehmen
                        for pr in reversed(doc.parse_runs):
                            if pr.raw_text:
                                raw_text = pr.raw_text
                                break

                    for error in match.solution_entry.errors:
                        error_id = f"solution_{solution_file_id}_{match.document_id}_{error.feature_id}"
                        vectorstore.add_error_example(
                            error_id=error_id,
                            error_type=error.error_type,
                            feature_id=error.feature_id,
                            context_text=raw_text[:2000] if raw_text else "",
                            wrong_value=error.current_value or "",
                            correct_value=error.expected_value or "",
                            reasoning=error.message or "",
                            ruleset_id=match.solution_entry.ruleset_id or "DE_USTG",
                        )
                        rag_created += 1
                except Exception as e:
                    logger.warning(f"Fehler beim Erstellen von RAG-Beispielen: {e}")

                solution_match.rag_examples_created = rag_created
                total_rag_examples += rag_created

            corrections.append(
                AppliedCorrectionSchema(
                    document_id=match.document_id,
                    document_filename=match.document_filename,
                    errors_applied=len(match.solution_entry.errors),
                    fields_updated=len(match.solution_entry.fields),
                    rag_examples_created=rag_created,
                    status="applied",
                )
            )
            applied_count += 1

        except Exception as e:
            logger.exception(f"Fehler beim Anwenden für {match.document_id}: {e}")
            errors.append(f"{match.document_filename}: {e}")
            skipped_count += 1

    # Lösungsdatei als angewendet markieren
    solution_file.applied = True
    solution_file.applied_at = datetime.utcnow()
    solution_file.applied_count = applied_count
    solution_file.skipped_count = skipped_count
    solution_file.rag_examples_created = total_rag_examples

    await session.commit()

    logger.info(
        f"Lösungsdatei {solution_file_id} angewendet: "
        f"{applied_count} angewendet, {skipped_count} übersprungen"
    )

    return SolutionApplyResponse(
        solution_file_id=solution_file_id,
        project_id=project_id,
        applied_count=applied_count,
        skipped_count=skipped_count,
        error_count=len(errors),
        rag_examples_created=total_rag_examples,
        corrections=corrections,
        errors=errors,
    )


@router.get(
    "/projects/{project_id}/solutions/{solution_file_id}",
)
async def get_solution_file(
    project_id: str,
    solution_file_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Gibt Details einer Lösungsdatei zurück.

    Args:
        project_id: Projekt-ID
        solution_file_id: Lösungsdatei-ID

    Returns:
        Lösungsdatei-Details
    """
    result = await session.execute(
        select(SolutionFile).where(
            SolutionFile.id == solution_file_id,
            SolutionFile.project_id == project_id,
        )
    )
    solution_file = result.scalar_one_or_none()
    if not solution_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lösungsdatei nicht gefunden",
        )

    return {
        "id": solution_file.id,
        "project_id": solution_file.project_id,
        "filename": solution_file.filename,
        "format": solution_file.format,
        "file_size": solution_file.file_size,
        "generator_version": solution_file.generator_version,
        "generated_at": solution_file.generated_at,
        "entry_count": solution_file.entry_count,
        "valid_count": solution_file.valid_count,
        "invalid_count": solution_file.invalid_count,
        "error_count": solution_file.error_count,
        "applied": solution_file.applied,
        "applied_at": solution_file.applied_at,
        "applied_count": solution_file.applied_count,
        "skipped_count": solution_file.skipped_count,
        "rag_examples_created": solution_file.rag_examples_created,
        "created_at": solution_file.created_at,
        "entries": solution_file.entries,
    }


@router.delete(
    "/projects/{project_id}/solutions/{solution_file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_solution_file(
    project_id: str,
    solution_file_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Löscht eine Lösungsdatei.

    Args:
        project_id: Projekt-ID
        solution_file_id: Lösungsdatei-ID
    """
    result = await session.execute(
        select(SolutionFile).where(
            SolutionFile.id == solution_file_id,
            SolutionFile.project_id == project_id,
        )
    )
    solution_file = result.scalar_one_or_none()
    if not solution_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lösungsdatei nicht gefunden",
        )

    await session.delete(solution_file)
    await session.commit()

    logger.info(f"Lösungsdatei {solution_file_id} gelöscht")
