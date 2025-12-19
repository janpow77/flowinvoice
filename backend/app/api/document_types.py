# Pfad: /backend/app/api/document_types.py
"""
FlowAudit DocumentType Settings API

Endpoints für Dokumenttyp-Verwaltung mit Chunking-Konfiguration.
"""

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.document_type import DocumentTypeSettings, SYSTEM_DOCUMENT_TYPES
from app.schemas.document_type import (
    DocumentTypeCreate,
    DocumentTypeListResponse,
    DocumentTypeResponse,
    DocumentTypeUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_system_types(session: AsyncSession) -> None:
    """
    Stellt sicher, dass System-Dokumenttypen existieren.
    Wird beim ersten API-Aufruf ausgeführt.
    """
    for type_data in SYSTEM_DOCUMENT_TYPES:
        result = await session.execute(
            select(DocumentTypeSettings).where(
                DocumentTypeSettings.slug == type_data["slug"]
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            doc_type = DocumentTypeSettings(
                id=str(uuid4()),
                **type_data,
            )
            session.add(doc_type)
            logger.info(f"Created system document type: {type_data['slug']}")

    await session.commit()


@router.get(
    "/settings/document-types",
    response_model=DocumentTypeListResponse,
)
async def list_document_types(
    session: AsyncSession = Depends(get_async_session),
) -> DocumentTypeListResponse:
    """
    Listet alle Dokumenttypen auf.

    Returns:
        Liste aller Dokumenttypen mit Chunking-Konfiguration.
    """
    # System-Typen sicherstellen
    await ensure_system_types(session)

    result = await session.execute(
        select(DocumentTypeSettings).order_by(
            DocumentTypeSettings.is_system.desc(),
            DocumentTypeSettings.name,
        )
    )
    doc_types = result.scalars().all()

    return DocumentTypeListResponse(
        data=[
            DocumentTypeResponse(
                id=dt.id,
                slug=dt.slug,
                name=dt.name,
                description=dt.description,
                is_system=dt.is_system,
                chunk_size_tokens=dt.chunk_size_tokens,
                chunk_overlap_tokens=dt.chunk_overlap_tokens,
                max_chunks=dt.max_chunks,
                chunk_strategy=dt.chunk_strategy,
                created_at=dt.created_at,
                updated_at=dt.updated_at,
            )
            for dt in doc_types
        ],
        total=len(doc_types),
    )


@router.get(
    "/settings/document-types/{doc_type_id}",
    response_model=DocumentTypeResponse,
)
async def get_document_type(
    doc_type_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> DocumentTypeResponse:
    """
    Gibt einen Dokumenttyp zurück.

    Args:
        doc_type_id: ID oder Slug des Dokumenttyps

    Returns:
        Dokumenttyp-Details.
    """
    # Suche nach ID oder Slug
    result = await session.execute(
        select(DocumentTypeSettings).where(
            (DocumentTypeSettings.id == doc_type_id)
            | (DocumentTypeSettings.slug == doc_type_id)
        )
    )
    doc_type = result.scalar_one_or_none()

    if not doc_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document type {doc_type_id} not found",
        )

    return DocumentTypeResponse(
        id=doc_type.id,
        slug=doc_type.slug,
        name=doc_type.name,
        description=doc_type.description,
        is_system=doc_type.is_system,
        chunk_size_tokens=doc_type.chunk_size_tokens,
        chunk_overlap_tokens=doc_type.chunk_overlap_tokens,
        max_chunks=doc_type.max_chunks,
        chunk_strategy=doc_type.chunk_strategy,
        created_at=doc_type.created_at,
        updated_at=doc_type.updated_at,
    )


@router.post(
    "/settings/document-types",
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentTypeResponse,
)
async def create_document_type(
    data: DocumentTypeCreate,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> DocumentTypeResponse:
    """
    Erstellt einen neuen Dokumenttyp.

    Args:
        data: Dokumenttyp-Daten

    Returns:
        Erstellter Dokumenttyp.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    # Slug-Duplikat prüfen
    result = await session.execute(
        select(DocumentTypeSettings).where(DocumentTypeSettings.slug == data.slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document type with slug '{data.slug}' already exists",
        )

    doc_type = DocumentTypeSettings(
        id=str(uuid4()),
        slug=data.slug,
        name=data.name,
        description=data.description,
        is_system=False,
        chunk_size_tokens=data.chunk_size_tokens,
        chunk_overlap_tokens=data.chunk_overlap_tokens,
        max_chunks=data.max_chunks,
        chunk_strategy=data.chunk_strategy,
    )

    session.add(doc_type)
    await session.commit()
    await session.refresh(doc_type)

    logger.info(f"Created document type: {doc_type.slug}")

    return DocumentTypeResponse(
        id=doc_type.id,
        slug=doc_type.slug,
        name=doc_type.name,
        description=doc_type.description,
        is_system=doc_type.is_system,
        chunk_size_tokens=doc_type.chunk_size_tokens,
        chunk_overlap_tokens=doc_type.chunk_overlap_tokens,
        max_chunks=doc_type.max_chunks,
        chunk_strategy=doc_type.chunk_strategy,
        created_at=doc_type.created_at,
        updated_at=doc_type.updated_at,
    )


@router.put(
    "/settings/document-types/{doc_type_id}",
    response_model=DocumentTypeResponse,
)
async def update_document_type(
    doc_type_id: str,
    data: DocumentTypeUpdate,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> DocumentTypeResponse:
    """
    Aktualisiert einen Dokumenttyp.

    Args:
        doc_type_id: ID oder Slug des Dokumenttyps
        data: Update-Daten

    Returns:
        Aktualisierter Dokumenttyp.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    result = await session.execute(
        select(DocumentTypeSettings).where(
            (DocumentTypeSettings.id == doc_type_id)
            | (DocumentTypeSettings.slug == doc_type_id)
        )
    )
    doc_type = result.scalar_one_or_none()

    if not doc_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document type {doc_type_id} not found",
        )

    # Felder aktualisieren (nur wenn gesetzt)
    if data.name is not None:
        doc_type.name = data.name
    if data.description is not None:
        doc_type.description = data.description
    if data.chunk_size_tokens is not None:
        doc_type.chunk_size_tokens = data.chunk_size_tokens
    if data.chunk_overlap_tokens is not None:
        doc_type.chunk_overlap_tokens = data.chunk_overlap_tokens
    if data.max_chunks is not None:
        doc_type.max_chunks = data.max_chunks
    if data.chunk_strategy is not None:
        doc_type.chunk_strategy = data.chunk_strategy

    await session.commit()
    await session.refresh(doc_type)

    logger.info(f"Updated document type: {doc_type.slug}")

    return DocumentTypeResponse(
        id=doc_type.id,
        slug=doc_type.slug,
        name=doc_type.name,
        description=doc_type.description,
        is_system=doc_type.is_system,
        chunk_size_tokens=doc_type.chunk_size_tokens,
        chunk_overlap_tokens=doc_type.chunk_overlap_tokens,
        max_chunks=doc_type.max_chunks,
        chunk_strategy=doc_type.chunk_strategy,
        created_at=doc_type.created_at,
        updated_at=doc_type.updated_at,
    )


@router.delete(
    "/settings/document-types/{doc_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document_type(
    doc_type_id: str,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> None:
    """
    Löscht einen Dokumenttyp.

    System-Dokumenttypen können nicht gelöscht werden.

    Args:
        doc_type_id: ID oder Slug des Dokumenttyps
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    result = await session.execute(
        select(DocumentTypeSettings).where(
            (DocumentTypeSettings.id == doc_type_id)
            | (DocumentTypeSettings.slug == doc_type_id)
        )
    )
    doc_type = result.scalar_one_or_none()

    if not doc_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document type {doc_type_id} not found",
        )

    if doc_type.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system document type",
        )

    await session.delete(doc_type)
    await session.commit()

    logger.info(f"Deleted document type: {doc_type.slug}")
