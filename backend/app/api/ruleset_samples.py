# Pfad: /backend/app/api/ruleset_samples.py
"""
FlowAudit Ruleset Samples API

Endpoints für Musterdokumente von Regelwerken.
"""

import hashlib
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_async_session
from app.models.enums import SampleStatus
from app.models.ruleset import Ruleset
from app.models.ruleset_sample import RulesetSample
from app.rag.vectorstore import get_vectorstore
from app.schemas.ruleset_sample import (
    RulesetSampleListItem,
    RulesetSampleListResponse,
    RulesetSampleResponse,
    RulesetSampleUpdate,
    SampleApproveRequest,
    SampleRejectRequest,
)
from app.services.parser import get_parser

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


@router.post(
    "/rulesets/{ruleset_id}/samples",
    status_code=status.HTTP_201_CREATED,
    response_model=RulesetSampleResponse,
)
async def upload_sample(
    ruleset_id: str,
    file: UploadFile = File(...),
    description: str = Form(default=None),
    ruleset_version: str = Form(default="1.0.0"),
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> RulesetSampleResponse:
    """
    Lädt ein Musterdokument für ein Regelwerk hoch.

    Das Dokument wird automatisch geparst und die extrahierten
    Daten als vorgeschlagene Ground Truth gespeichert.

    Args:
        ruleset_id: Ruleset-ID
        file: PDF-Datei
        description: Optionale Beschreibung
        ruleset_version: Ruleset-Version

    Returns:
        Hochgeladenes Sample mit extrahierten Daten.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    # Ruleset prüfen
    result = await session.execute(
        select(Ruleset).where(
            Ruleset.ruleset_id == ruleset_id,
            Ruleset.version == ruleset_version,
        )
    )
    ruleset = result.scalar_one_or_none()

    if not ruleset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruleset {ruleset_id} v{ruleset_version} not found",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename required",
        )

    # Datei lesen und Hash berechnen
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()

    # Duplikat-Check
    existing = await session.execute(
        select(RulesetSample).where(
            RulesetSample.ruleset_id == ruleset_id,
            RulesetSample.file_hash == sha256,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sample with same content already exists",
        )

    # Speicherpfad erstellen
    sample_id = str(uuid4())
    storage_dir = settings.uploads_path / "samples" / ruleset_id
    storage_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{sample_id}_{file.filename}"
    storage_path = storage_dir / filename

    # Datei speichern
    async with aiofiles.open(storage_path, "wb") as f:
        await f.write(content)

    # Sample erstellen
    sample = RulesetSample(
        id=sample_id,
        ruleset_id=ruleset_id,
        ruleset_version=ruleset_version,
        filename=file.filename,
        file_path=str(storage_path),
        file_hash=sha256,
        file_size=len(content),
        mime_type=file.content_type or "application/pdf",
        description=description,
        status=SampleStatus.PROCESSING,
    )

    session.add(sample)
    await session.flush()

    # Automatisch parsen
    try:
        parser = get_parser()
        parse_result = await parser.parse_pdf(storage_path)

        sample.raw_text = parse_result.raw_text
        sample.extracted_data = {
            k: {"value": v.value, "confidence": v.confidence, "raw_text": v.raw_text}
            for k, v in parse_result.extracted.items()
        }
        sample.status = SampleStatus.PENDING_REVIEW
        sample.processed_at = datetime.utcnow()

        logger.info(f"Sample {sample_id} parsed successfully")

    except Exception as e:
        logger.error(f"Error parsing sample {sample_id}: {e}")
        sample.status = SampleStatus.PENDING_REVIEW  # Trotzdem reviewbar
        sample.parse_error = str(e)

    await session.flush()

    return RulesetSampleResponse(
        id=sample.id,
        ruleset_id=sample.ruleset_id,
        ruleset_version=sample.ruleset_version,
        filename=sample.filename,
        file_size=sample.file_size,
        mime_type=sample.mime_type,
        description=sample.description,
        status=sample.status,
        extracted_data=sample.extracted_data,
        ground_truth=sample.ground_truth,
        parse_error=sample.parse_error,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
        processed_at=sample.processed_at,
        approved_at=sample.approved_at,
    )


@router.get(
    "/rulesets/{ruleset_id}/samples",
    response_model=RulesetSampleListResponse,
)
async def list_samples(
    ruleset_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> RulesetSampleListResponse:
    """
    Listet alle Musterdokumente für ein Regelwerk.

    Args:
        ruleset_id: Ruleset-ID

    Returns:
        Liste der Samples mit Status-Statistik.
    """
    result = await session.execute(
        select(RulesetSample)
        .where(RulesetSample.ruleset_id == ruleset_id)
        .order_by(RulesetSample.created_at.desc())
    )
    samples = result.scalars().all()

    # Status-Statistik
    stats: dict[str, int] = {}
    for s in SampleStatus:
        count = sum(1 for sample in samples if sample.status == s)
        if count > 0:
            stats[s.value] = count

    items = [
        RulesetSampleListItem(
            id=s.id,
            filename=s.filename,
            description=s.description,
            status=s.status,
            created_at=s.created_at,
            has_ground_truth=s.has_ground_truth,
        )
        for s in samples
    ]

    return RulesetSampleListResponse(
        data=items,
        total=len(items),
        stats=stats,
    )


@router.get(
    "/rulesets/{ruleset_id}/samples/{sample_id}",
    response_model=RulesetSampleResponse,
)
async def get_sample(
    ruleset_id: str,
    sample_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> RulesetSampleResponse:
    """
    Gibt Details eines Samples zurück.

    Args:
        ruleset_id: Ruleset-ID
        sample_id: Sample-ID

    Returns:
        Sample-Details mit extrahierten Daten und Ground Truth.
    """
    result = await session.execute(
        select(RulesetSample).where(
            RulesetSample.id == sample_id,
            RulesetSample.ruleset_id == ruleset_id,
        )
    )
    sample = result.scalar_one_or_none()

    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample {sample_id} not found",
        )

    return RulesetSampleResponse(
        id=sample.id,
        ruleset_id=sample.ruleset_id,
        ruleset_version=sample.ruleset_version,
        filename=sample.filename,
        file_size=sample.file_size,
        mime_type=sample.mime_type,
        description=sample.description,
        status=sample.status,
        extracted_data=sample.extracted_data,
        ground_truth=sample.ground_truth,
        parse_error=sample.parse_error,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
        processed_at=sample.processed_at,
        approved_at=sample.approved_at,
    )


@router.put(
    "/rulesets/{ruleset_id}/samples/{sample_id}",
    response_model=RulesetSampleResponse,
)
async def update_sample(
    ruleset_id: str,
    sample_id: str,
    data: RulesetSampleUpdate,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> RulesetSampleResponse:
    """
    Aktualisiert Ground Truth eines Samples.

    Args:
        ruleset_id: Ruleset-ID
        sample_id: Sample-ID
        data: Update-Daten

    Returns:
        Aktualisiertes Sample.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    result = await session.execute(
        select(RulesetSample).where(
            RulesetSample.id == sample_id,
            RulesetSample.ruleset_id == ruleset_id,
        )
    )
    sample = result.scalar_one_or_none()

    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample {sample_id} not found",
        )

    if data.description is not None:
        sample.description = data.description

    if data.ground_truth is not None:
        sample.ground_truth = data.ground_truth

    await session.flush()

    return RulesetSampleResponse(
        id=sample.id,
        ruleset_id=sample.ruleset_id,
        ruleset_version=sample.ruleset_version,
        filename=sample.filename,
        file_size=sample.file_size,
        mime_type=sample.mime_type,
        description=sample.description,
        status=sample.status,
        extracted_data=sample.extracted_data,
        ground_truth=sample.ground_truth,
        parse_error=sample.parse_error,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
        processed_at=sample.processed_at,
        approved_at=sample.approved_at,
    )


@router.post(
    "/rulesets/{ruleset_id}/samples/{sample_id}/approve",
    response_model=RulesetSampleResponse,
)
async def approve_sample(
    ruleset_id: str,
    sample_id: str,
    data: SampleApproveRequest | None = None,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> RulesetSampleResponse:
    """
    Genehmigt ein Sample und erstellt RAG-Beispiele.

    Nach Approval werden die Ground-Truth-Daten als hochwertige
    Trainingsbeispiele in ChromaDB gespeichert.

    Args:
        ruleset_id: Ruleset-ID
        sample_id: Sample-ID
        data: Optional finale Ground Truth

    Returns:
        Genehmigtes Sample.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    result = await session.execute(
        select(RulesetSample).where(
            RulesetSample.id == sample_id,
            RulesetSample.ruleset_id == ruleset_id,
        )
    )
    sample = result.scalar_one_or_none()

    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample {sample_id} not found",
        )

    if sample.status == SampleStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sample already approved",
        )

    # Ground Truth aktualisieren falls mitgeliefert
    if data and data.ground_truth:
        sample.ground_truth = data.ground_truth
    elif not sample.ground_truth:
        # Extrahierte Daten als Ground Truth übernehmen
        if sample.extracted_data:
            sample.ground_truth = {
                k: v.get("value") if isinstance(v, dict) else v
                for k, v in sample.extracted_data.items()
            }

    # Status aktualisieren
    sample.status = SampleStatus.APPROVED
    sample.approved_at = datetime.utcnow()

    # RAG-Beispiele erstellen
    rag_example_ids: list[str] = []
    try:
        vectorstore = get_vectorstore()

        # Sample als Invoice-Beispiel hinzufügen
        example_id = f"sample_{sample.id}"
        vectorstore.add_invoice_example(
            invoice_id=example_id,
            raw_text=sample.raw_text or "",
            extracted_data=sample.ground_truth or {},
            assessment="ACCEPTED",
            errors=[],
            ruleset_id=sample.ruleset_id,
        )
        rag_example_ids.append(example_id)

        logger.info(f"Created RAG example for sample {sample_id}")

    except Exception as e:
        logger.error(f"Error creating RAG examples for sample {sample_id}: {e}")
        # Nicht abbrechen, Sample ist trotzdem approved

    sample.rag_example_ids = rag_example_ids
    await session.flush()

    return RulesetSampleResponse(
        id=sample.id,
        ruleset_id=sample.ruleset_id,
        ruleset_version=sample.ruleset_version,
        filename=sample.filename,
        file_size=sample.file_size,
        mime_type=sample.mime_type,
        description=sample.description,
        status=sample.status,
        extracted_data=sample.extracted_data,
        ground_truth=sample.ground_truth,
        parse_error=sample.parse_error,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
        processed_at=sample.processed_at,
        approved_at=sample.approved_at,
    )


@router.post(
    "/rulesets/{ruleset_id}/samples/{sample_id}/reject",
    response_model=RulesetSampleResponse,
)
async def reject_sample(
    ruleset_id: str,
    sample_id: str,
    data: SampleRejectRequest | None = None,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> RulesetSampleResponse:
    """
    Lehnt ein Sample ab.

    Args:
        ruleset_id: Ruleset-ID
        sample_id: Sample-ID
        data: Optional Ablehnungsgrund

    Returns:
        Abgelehntes Sample.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    result = await session.execute(
        select(RulesetSample).where(
            RulesetSample.id == sample_id,
            RulesetSample.ruleset_id == ruleset_id,
        )
    )
    sample = result.scalar_one_or_none()

    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample {sample_id} not found",
        )

    sample.status = SampleStatus.REJECTED
    if data and data.reason:
        sample.parse_error = f"Rejected: {data.reason}"

    await session.flush()

    return RulesetSampleResponse(
        id=sample.id,
        ruleset_id=sample.ruleset_id,
        ruleset_version=sample.ruleset_version,
        filename=sample.filename,
        file_size=sample.file_size,
        mime_type=sample.mime_type,
        description=sample.description,
        status=sample.status,
        extracted_data=sample.extracted_data,
        ground_truth=sample.ground_truth,
        parse_error=sample.parse_error,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
        processed_at=sample.processed_at,
        approved_at=sample.approved_at,
    )


@router.delete(
    "/rulesets/{ruleset_id}/samples/{sample_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_sample(
    ruleset_id: str,
    sample_id: str,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> None:
    """
    Löscht ein Sample.

    Args:
        ruleset_id: Ruleset-ID
        sample_id: Sample-ID
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    result = await session.execute(
        select(RulesetSample).where(
            RulesetSample.id == sample_id,
            RulesetSample.ruleset_id == ruleset_id,
        )
    )
    sample = result.scalar_one_or_none()

    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample {sample_id} not found",
        )

    # TODO: Auch RAG-Beispiele löschen falls vorhanden

    await session.delete(sample)
    await session.flush()
