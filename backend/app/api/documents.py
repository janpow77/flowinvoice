# Pfad: /backend/app/api/documents.py
"""
FlowAudit Documents API

Endpoints für Dokumente (Rechnungen), Upload, Parse, Precheck.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_async_session
from app.models.document import Document, ParseRun, PrecheckRun
from app.models.enums import DocumentStatus
from app.models.project import Project
from app.schemas.document import (
    DocumentListItem,
    DocumentResponse,
    DocumentUploadItem,
    DocumentUploadResponse,
    ParseRunResponse,
    PrecheckRunResponse,
)

router = APIRouter()
settings = get_settings()


@router.post(
    "/projects/{project_id}/documents/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents(
    project_id: str,
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_async_session),
) -> DocumentUploadResponse:
    """
    Lädt Dokumente hoch.

    Args:
        project_id: Projekt-ID
        files: PDF-Dateien

    Returns:
        Liste der hochgeladenen Dokumente.
    """
    # Projekt prüfen
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    uploaded: list[DocumentUploadItem] = []

    for file in files:
        if not file.filename:
            continue

        # Datei lesen und Hash berechnen
        content = await file.read()
        sha256 = hashlib.sha256(content).hexdigest()

        # Duplikat-Check im Projekt
        existing = await session.execute(
            select(Document).where(
                Document.project_id == project_id,
                Document.sha256 == sha256,
            )
        )
        is_duplicate = existing.scalar_one_or_none() is not None

        # Speicherpfad
        doc_id = str(uuid4())
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        storage_dir = settings.uploads_path / date_prefix
        storage_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{doc_id}_{file.filename}"
        storage_path = storage_dir / filename

        # Datei speichern
        async with aiofiles.open(storage_path, "wb") as f:
            await f.write(content)

        # Dokument erstellen
        document = Document(
            id=doc_id,
            project_id=project_id,
            filename=filename,
            original_filename=file.filename,
            sha256=sha256,
            file_size_bytes=len(content),
            storage_path=str(storage_path),
            status=DocumentStatus.UPLOADED,
            ruleset_id=project.ruleset_id_hint,
            ui_language=project.ui_language_hint,
        )

        session.add(document)

        uploaded.append(
            DocumentUploadItem(
                document_id=doc_id,
                filename=file.filename,
                sha256=sha256,
                status=DocumentStatus.UPLOADED,
                is_duplicate_in_project=is_duplicate,
            )
        )

    await session.flush()

    return DocumentUploadResponse(data=uploaded)


@router.get("/projects/{project_id}/documents")
async def list_documents(
    project_id: str,
    document_status: DocumentStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Listet Dokumente eines Projekts.

    Args:
        project_id: Projekt-ID
        status: Optional Status-Filter
        limit: Max. Anzahl
        offset: Offset

    Returns:
        Paginierte Liste der Dokumente.
    """
    query = select(Document).where(Document.project_id == project_id)

    if document_status:
        query = query.where(Document.status == document_status)

    # Total
    count_query = select(func.count(Document.id)).where(Document.project_id == project_id)
    if document_status:
        count_query = count_query.where(Document.status == document_status)
    total = await session.scalar(count_query) or 0

    # Paginated
    query = query.order_by(Document.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    documents = result.scalars().all()

    data = [
        DocumentListItem(
            document_id=d.id,
            filename=d.original_filename,
            status=d.status,
            ruleset_id=d.ruleset_id,
            created_at=d.created_at,
        )
        for d in documents
    ]

    return {
        "data": [item.model_dump() for item in data],
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> DocumentResponse:
    """
    Gibt Dokument-Details zurück.

    Args:
        document_id: Dokument-ID

    Returns:
        Dokument-Details.
    """
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    return DocumentResponse(
        id=document.id,
        project_id=document.project_id,
        filename=document.filename,
        original_filename=document.original_filename,
        sha256=document.sha256,
        file_size_bytes=document.file_size_bytes,
        status=document.status,
        ruleset_id=document.ruleset_id,
        ruleset_version=document.ruleset_version,
        ui_language=document.ui_language,
        error_message=document.error_message,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.get("/documents/{document_id}/file")
async def get_document_file(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Gibt Original-PDF zurück.

    Args:
        document_id: Dokument-ID

    Returns:
        PDF-Stream.
    """
    from fastapi.responses import FileResponse

    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    file_path = Path(document.storage_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=document.original_filename,
    )


@router.post("/documents/{document_id}/parse", status_code=status.HTTP_202_ACCEPTED)
async def start_parse(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Startet PDF-Parsing.

    Args:
        document_id: Dokument-ID

    Returns:
        Parse-Run-Info.
    """
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Parse-Run erstellen
    parse_run = ParseRun(
        document_id=document_id,
        engine="HYBRID",
        status="PENDING",
    )

    session.add(parse_run)
    document.status = DocumentStatus.PARSING
    await session.flush()

    # TODO: Celery Task starten
    # parse_document_task.delay(document_id, parse_run.id)

    return {
        "document_id": document_id,
        "status": "PARSING",
        "parse_run_id": parse_run.id,
    }


@router.get("/parse-runs/{parse_run_id}")
async def get_parse_run(
    parse_run_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> ParseRunResponse:
    """
    Gibt Parse-Run-Details zurück.

    Args:
        parse_run_id: Parse-Run-ID

    Returns:
        Parse-Run-Details.
    """
    result = await session.execute(select(ParseRun).where(ParseRun.id == parse_run_id))
    parse_run = result.scalar_one_or_none()

    if not parse_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ParseRun {parse_run_id} not found",
        )

    outputs = None
    if parse_run.raw_text:
        outputs = {
            "raw_text_len": len(parse_run.raw_text),
            "pages": len(parse_run.pages) if parse_run.pages else 0,
        }

    return ParseRunResponse(
        id=parse_run.id,
        document_id=parse_run.document_id,
        engine=parse_run.engine,
        status=parse_run.status,
        timings_ms=parse_run.timings_ms,
        outputs=outputs,
        error_message=parse_run.error_message,
        created_at=parse_run.created_at,
        completed_at=parse_run.completed_at,
    )


@router.post("/documents/{document_id}/precheck", status_code=status.HTTP_202_ACCEPTED)
async def start_precheck(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Startet Precheck (deterministische Regelprüfung).

    Args:
        document_id: Dokument-ID

    Returns:
        Precheck-Run-Info.
    """
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Precheck-Run erstellen
    precheck_run = PrecheckRun(
        document_id=document_id,
        status="PENDING",
        checks=[],
    )

    session.add(precheck_run)
    await session.flush()

    # TODO: Celery Task starten
    # precheck_document_task.delay(document_id, precheck_run.id)

    return {
        "precheck_run_id": precheck_run.id,
        "document_id": document_id,
        "status": "RUNNING",
    }


@router.get("/precheck-runs/{precheck_run_id}")
async def get_precheck_run(
    precheck_run_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> PrecheckRunResponse:
    """
    Gibt Precheck-Run-Details zurück.

    Args:
        precheck_run_id: Precheck-Run-ID

    Returns:
        Precheck-Run mit Checks.
    """
    result = await session.execute(
        select(PrecheckRun).where(PrecheckRun.id == precheck_run_id)
    )
    precheck_run = result.scalar_one_or_none()

    if not precheck_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PrecheckRun {precheck_run_id} not found",
        )

    return PrecheckRunResponse(
        id=precheck_run.id,
        document_id=precheck_run.document_id,
        status=precheck_run.status,
        checks=precheck_run.checks,
        error_message=precheck_run.error_message,
        created_at=precheck_run.created_at,
        completed_at=precheck_run.completed_at,
    )
