# Pfad: /backend/app/api/documents.py
"""
FlowAudit Documents API

Endpoints für Dokumente (Rechnungen), Upload, Parse, Precheck.
"""

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_async_session
from app.models.document import Document, ParseRun, PrecheckRun
from app.models.enums import DocumentStatus, DocumentType
from app.models.project import Project
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentListItem,
    DocumentResponse,
    DocumentUploadItem,
    DocumentUploadResponse,
    ParseRunResponse,
    PrecheckRunResponse,
)
from app.services.audit import get_audit_service
from app.worker.tasks import analyze_document_task, process_document_task

router = APIRouter()
audit = get_audit_service()
settings = get_settings()


@router.post(
    "/projects/{project_id}/documents/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents(
    project_id: str,
    files: list[UploadFile] = File(...),
    document_type: str = Form(default="INVOICE"),
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

        # DocumentType validieren
        try:
            doc_type = DocumentType(document_type)
        except ValueError:
            doc_type = DocumentType.INVOICE

        # Dokument erstellen
        document = Document(
            id=doc_id,
            project_id=project_id,
            filename=filename,
            original_filename=file.filename,
            sha256=sha256,
            file_size_bytes=len(content),
            storage_path=str(storage_path),
            document_type=doc_type,
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

    try:
        await session.flush()

        # Audit-Logging für alle Uploads
        for item in uploaded:
            await audit.log_document_access(
                document_id=item.document_id,
                filename=item.filename,
                action="uploaded",
                session=session,
            )

        await session.commit()

    except IntegrityError as e:
        await session.rollback()
        # Race Condition: Dokument wurde bereits hochgeladen
        if "uq_document_project_sha256" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ein oder mehrere Dokumente existieren bereits in diesem Projekt (Duplikat anhand SHA-256 erkannt).",
            ) from None
        raise

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
        Dokument-Details inkl. Extraktion, Precheck und Analyse.
    """
    from app.models.result import AnalysisResult
    from app.schemas.document import AnalysisResultResponse

    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Audit: Dokument wurde angesehen
    await audit.log_document_access(
        document_id=document_id,
        filename=document.original_filename,
        action="viewed",
    )

    # Neuestes Analyse-Ergebnis laden
    analysis_result_response = None
    analysis_query = await session.execute(
        select(AnalysisResult)
        .where(AnalysisResult.document_id == document_id)
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    analysis_result = analysis_query.scalar_one_or_none()

    if analysis_result:
        analysis_result_response = AnalysisResultResponse(
            id=analysis_result.id,
            provider=analysis_result.provider.value if analysis_result.provider else "unknown",
            model=analysis_result.model,
            overall_assessment=analysis_result.overall_assessment,
            confidence=analysis_result.confidence,
            semantic_check=analysis_result.semantic_check,
            economic_check=analysis_result.economic_check,
            beneficiary_match=analysis_result.beneficiary_match,
            warnings=analysis_result.warnings or [],
            input_tokens=analysis_result.input_tokens,
            output_tokens=analysis_result.output_tokens,
            latency_ms=analysis_result.latency_ms,
            created_at=analysis_result.created_at,
        )

    # Precheck-Fehler aus letztem PrecheckRun laden
    precheck_errors = None
    precheck_passed = document.precheck_passed

    precheck_query = await session.execute(
        select(PrecheckRun)
        .where(PrecheckRun.document_id == document_id)
        .order_by(PrecheckRun.created_at.desc())
        .limit(1)
    )
    precheck_run = precheck_query.scalar_one_or_none()

    if precheck_run and precheck_run.checks:
        # Nur Fehler und Warnungen extrahieren (status != OK)
        precheck_errors = [
            {
                "feature_id": check.get("feature_id", "unknown"),
                "severity": check.get("severity", "LOW"),
                "message": check.get("message", ""),
                "status": check.get("status", "UNKNOWN"),
            }
            for check in precheck_run.checks
            if check.get("status") in ("FAIL", "WARN", "ERROR")
        ]

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
        # Erweiterte Felder
        extracted_data=document.extracted_data,
        precheck_passed=precheck_passed,
        precheck_errors=precheck_errors,
        analysis_result=analysis_result_response,
    )


@router.get("/documents/{document_id}/llm-runs")
async def get_document_llm_runs(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Gibt LLM-Runs für ein Dokument zurück.

    Args:
        document_id: Dokument-ID

    Returns:
        Liste der LLM-Runs mit Statistiken.
    """
    from app.models.llm import LlmRun
    from app.schemas.document import LlmRunItem, LlmRunListResponse, LlmRunStats

    # Dokument prüfen
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # LLM-Runs laden
    runs_result = await session.execute(
        select(LlmRun)
        .where(LlmRun.document_id == document_id)
        .order_by(LlmRun.created_at.desc())
    )
    runs = runs_result.scalars().all()

    # Response bauen
    run_items = []
    for run in runs:
        stats = LlmRunStats(
            duration_ms=run.duration_ms,
            input_tokens=run.input_tokens,
            output_tokens=run.output_tokens,
        )
        run_items.append(
            LlmRunItem(
                id=run.id,
                provider=run.provider.value,
                model_name=run.model_name,
                status=run.status,
                stats=stats,
                error_message=run.error_message,
                created_at=run.created_at,
                completed_at=run.completed_at,
            )
        )

    return LlmRunListResponse(data=run_items, total=len(run_items))


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

    # Audit: Dokument wurde heruntergeladen
    await audit.log_document_access(
        document_id=document_id,
        filename=document.original_filename,
        action="downloaded",
    )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=document.original_filename,
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> DocumentDeleteResponse:
    """
    Löscht ein Dokument inklusive Datei (DSGVO-Compliance).

    Args:
        document_id: Dokument-ID

    Returns:
        Löschbestätigung.
    """
    import os

    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    original_filename = document.original_filename
    storage_path = document.storage_path

    # Datei vom Dateisystem löschen
    file_deleted = False
    if storage_path:
        file_path = Path(storage_path)
        if file_path.exists():
            try:
                os.remove(file_path)
                file_deleted = True
            except OSError as e:
                # Fehler loggen, aber Löschung fortsetzen
                import logging
                logging.getLogger(__name__).error(
                    f"Konnte Datei nicht löschen: {file_path} - {e}"
                )

    # Zugehörige Parse-Runs löschen
    await session.execute(
        select(ParseRun).where(ParseRun.document_id == document_id)
    )
    parse_runs = await session.execute(
        select(ParseRun).where(ParseRun.document_id == document_id)
    )
    for pr in parse_runs.scalars().all():
        await session.delete(pr)

    # Zugehörige Precheck-Runs löschen
    precheck_runs = await session.execute(
        select(PrecheckRun).where(PrecheckRun.document_id == document_id)
    )
    for pcr in precheck_runs.scalars().all():
        await session.delete(pcr)

    # Dokument aus DB löschen
    await session.delete(document)

    # Audit-Log
    await audit.log_document_access(
        document_id=document_id,
        filename=original_filename,
        action="deleted",
        session=session,
    )

    await session.commit()

    return DocumentDeleteResponse(
        document_id=document_id,
        filename=original_filename,
        deleted=True,
        file_deleted=file_deleted,
        message="Dokument und zugehörige Daten erfolgreich gelöscht"
        if file_deleted
        else "Dokument gelöscht, Datei konnte nicht entfernt werden",
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
    await session.commit()

    # Celery Task für Parsing starten
    task = process_document_task.delay(document_id)

    return {
        "document_id": document_id,
        "status": "PARSING",
        "parse_run_id": parse_run.id,
        "task_id": task.id,
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


    from app.services.parser import ExtractedValue, ParsedPage, ParseResult
    from app.services.rule_engine import get_rule_engine

    # Parse-Run des Dokuments laden
    parse_run_result = await session.execute(
        select(ParseRun)
        .where(ParseRun.document_id == document_id)
        .order_by(ParseRun.created_at.desc())
        .limit(1)
    )
    parse_run = parse_run_result.scalar_one_or_none()

    if not parse_run or not parse_run.extracted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be parsed first before precheck",
        )

    # Precheck-Run erstellen
    precheck_run = PrecheckRun(
        document_id=document_id,
        status="RUNNING",
        checks=[],
    )
    session.add(precheck_run)
    await session.flush()

    try:
        # Parse-Result aus DB-Daten rekonstruieren
        extracted_values = {}
        for key, val in parse_run.extracted.items():
            if isinstance(val, dict):
                extracted_values[key] = ExtractedValue(
                    value=val.get("value"),
                    raw_text=val.get("raw_text", ""),
                    confidence=val.get("confidence", 0.0),
                )

        parse_result = ParseResult(
            raw_text=parse_run.raw_text or "",
            pages=[
                ParsedPage(
                    page_number=p.get("page_number", 1),
                    width=p.get("width", 612),
                    height=p.get("height", 792),
                    text=p.get("text", ""),
                    tokens=[],
                )
                for p in (parse_run.pages or [])
            ],
            extracted=extracted_values,
            timings_ms={},
        )

        # Rule Engine ausführen
        rule_engine = get_rule_engine(document.ruleset_id or "DE_USTG")
        precheck_result = rule_engine.precheck(parse_result)

        # Ergebnis speichern
        precheck_run.status = "COMPLETED"
        precheck_run.checks = [
            {
                "feature_id": c.feature_id,
                "status": c.status.value,
                "value": str(c.value) if c.value else None,
                "error_type": c.error_type.value if c.error_type else None,
                "severity": c.severity.value,
                "message": c.message,
                "legal_basis": c.legal_basis,
            }
            for c in precheck_result.checks
        ]
        precheck_run.completed_at = datetime.now(UTC)

        # Dokument-Status aktualisieren
        if precheck_result.passed:
            document.status = DocumentStatus.PRECHECKED
        else:
            document.status = DocumentStatus.FAILED

        await session.commit()

        return {
            "precheck_run_id": precheck_run.id,
            "document_id": document_id,
            "status": "COMPLETED",
            "passed": precheck_result.passed,
            "error_count": len(precheck_result.errors),
            "warning_count": len(precheck_result.warnings),
        }

    except Exception as e:
        precheck_run.status = "FAILED"
        precheck_run.error_message = str(e)
        await session.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Precheck failed: {e}",
        ) from e


@router.post("/documents/{document_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_document(
    document_id: str,
    provider: str | None = None,
    model: str | None = None,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Startet KI-Analyse für ein Dokument (kombiniert prepare + run).

    Args:
        document_id: Dokument-ID
        provider: LLM-Provider (optional, default LOCAL_OLLAMA)
        model: Modell-Name (optional, default llama3.1:8b-instruct-q4)

    Returns:
        Analyse-Info mit Run-ID.
    """
    from app.models.enums import Provider
    from app.models.llm import LlmRun, PreparePayload
    from app.services.rule_engine import RULESETS

    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # Prüfe ob Dokument geparst wurde (raw_text wird in Document gespeichert)
    if not document.raw_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be parsed first before analysis",
        )

    # PreparePayload erstellen
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

    payload = PreparePayload(
        document_id=document_id,
        schema_version="1.0",
        ruleset={
            "ruleset_id": ruleset_id,
            "version": document.ruleset_version or "1.0.0",
        },
        ui_language=document.ui_language,
        features=features_list,
        extracted_text=document.raw_text,
    )
    session.add(payload)
    await session.flush()

    # Provider/Model bestimmen
    llm_provider = Provider.LOCAL_OLLAMA
    if provider:
        try:
            llm_provider = Provider(provider)
        except ValueError:
            pass  # Fallback auf LOCAL_OLLAMA

    settings = get_settings()
    model_name = model or settings.ollama_default_model

    # LLM-Run erstellen
    llm_run = LlmRun(
        document_id=document_id,
        payload_id=payload.id,
        provider=llm_provider,
        model_name=model_name,
        status="PENDING",
    )
    session.add(llm_run)
    document.status = DocumentStatus.LLM_RUNNING
    await session.commit()

    # Celery Task für LLM-Analyse starten
    task = analyze_document_task.delay(document_id, llm_provider.value, model_name)

    return {
        "document_id": document_id,
        "llm_run_id": llm_run.id,
        "payload_id": payload.id,
        "status": "ANALYZING",
        "provider": llm_provider.value,
        "model": model_name,
        "task_id": task.id,
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
