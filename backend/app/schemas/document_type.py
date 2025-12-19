# Pfad: /backend/app/schemas/document_type.py
"""
FlowAudit DocumentType Schemas

Pydantic Schemas für Dokumenttyp-Einstellungen.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChunkingConfigSchema(BaseModel):
    """Schema für Chunking-Konfiguration."""

    model_config = ConfigDict(from_attributes=True)

    chunk_size_tokens: int = Field(
        default=700,
        ge=200,
        le=2000,
        description="Chunk-Größe in Tokens (200-2000)",
    )
    chunk_overlap_tokens: int = Field(
        default=120,
        ge=0,
        le=500,
        description="Überlappung in Tokens (0-500)",
    )
    max_chunks: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Maximale Anzahl Chunks (1-20)",
    )
    chunk_strategy: Literal["fixed", "paragraph", "semantic"] = Field(
        default="fixed",
        description="Chunking-Strategie",
    )


class DocumentTypeBase(BaseModel):
    """Basis-Schema für Dokumenttypen."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=100, description="Anzeigename")
    description: str | None = Field(default=None, description="Beschreibung")


class DocumentTypeCreate(DocumentTypeBase):
    """Schema für Dokumenttyp-Erstellung."""

    slug: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Eindeutiger Slug (lowercase, underscore erlaubt)",
    )
    chunk_size_tokens: int = Field(default=700, ge=200, le=2000)
    chunk_overlap_tokens: int = Field(default=120, ge=0, le=500)
    max_chunks: int = Field(default=6, ge=1, le=20)
    chunk_strategy: Literal["fixed", "paragraph", "semantic"] = Field(default="fixed")


class DocumentTypeUpdate(BaseModel):
    """Schema für Dokumenttyp-Update."""

    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None)
    chunk_size_tokens: int | None = Field(default=None, ge=200, le=2000)
    chunk_overlap_tokens: int | None = Field(default=None, ge=0, le=500)
    max_chunks: int | None = Field(default=None, ge=1, le=20)
    chunk_strategy: Literal["fixed", "paragraph", "semantic"] | None = Field(
        default=None
    )


class DocumentTypeResponse(BaseModel):
    """Response-Schema für Dokumenttyp."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID")
    slug: str = Field(..., description="Eindeutiger Slug")
    name: str = Field(..., description="Anzeigename")
    description: str | None = Field(default=None, description="Beschreibung")
    is_system: bool = Field(..., description="System-Typ (nicht löschbar)")

    # Chunking
    chunk_size_tokens: int = Field(..., description="Chunk-Größe in Tokens")
    chunk_overlap_tokens: int = Field(..., description="Überlappung in Tokens")
    max_chunks: int = Field(..., description="Maximale Anzahl Chunks")
    chunk_strategy: str = Field(..., description="Chunking-Strategie")

    # Zeitstempel
    created_at: datetime = Field(..., description="Erstellungszeitpunkt")
    updated_at: datetime = Field(..., description="Letztes Update")


class DocumentTypeListResponse(BaseModel):
    """Response für Dokumenttyp-Liste."""

    model_config = ConfigDict(from_attributes=True)

    data: list[DocumentTypeResponse] = Field(..., description="Liste der Dokumenttypen")
    total: int = Field(..., description="Gesamtanzahl")
