# Pfad: /backend/app/models/document_type.py
"""
FlowAudit DocumentType Settings Model

Dokumenttyp-Konfigurationen mit Chunking-Einstellungen.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DocumentTypeSettings(Base):
    """
    Dokumenttyp-Einstellungen mit Chunking-Konfiguration.

    Jeder Dokumenttyp kann eigene Chunking-Parameter haben,
    die beim RAG-Embedding und der Analyse verwendet werden.
    """

    __tablename__ = "document_type_settings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    # Identifikation
    slug: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # System-Flag (System-Typen können nicht gelöscht werden)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Chunking-Einstellungen
    chunk_size_tokens: Mapped[int] = mapped_column(Integer, default=700, nullable=False)
    chunk_overlap_tokens: Mapped[int] = mapped_column(
        Integer, default=120, nullable=False
    )
    max_chunks: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    chunk_strategy: Mapped[str] = mapped_column(
        String(20), default="fixed", nullable=False
    )

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<DocumentTypeSettings {self.slug} ({self.name})>"

    def to_chunking_dict(self) -> dict:
        """Gibt Chunking-Config als Dictionary zurück."""
        return {
            "chunk_size_tokens": self.chunk_size_tokens,
            "chunk_overlap_tokens": self.chunk_overlap_tokens,
            "max_chunks": self.max_chunks,
            "chunk_strategy": self.chunk_strategy,
        }


# System-Dokumenttypen (werden bei Migration eingefügt)
SYSTEM_DOCUMENT_TYPES = [
    {
        "slug": "invoice",
        "name": "Rechnung",
        "description": "Standard-Rechnungen und Belege",
        "is_system": True,
        "chunk_size_tokens": 700,
        "chunk_overlap_tokens": 120,
        "max_chunks": 6,
        "chunk_strategy": "fixed",
    },
    {
        "slug": "bank_statement",
        "name": "Kontoauszug",
        "description": "Bank- und Kontoauszüge",
        "is_system": True,
        "chunk_size_tokens": 900,
        "chunk_overlap_tokens": 150,
        "max_chunks": 6,
        "chunk_strategy": "fixed",
    },
    {
        "slug": "procurement",
        "name": "Vergabeunterlagen",
        "description": "Ausschreibungen und Vergabedokumente",
        "is_system": True,
        "chunk_size_tokens": 1100,
        "chunk_overlap_tokens": 180,
        "max_chunks": 8,
        "chunk_strategy": "fixed",
    },
    {
        "slug": "other",
        "name": "Sonstiges",
        "description": "Andere Dokumenttypen",
        "is_system": True,
        "chunk_size_tokens": 900,
        "chunk_overlap_tokens": 150,
        "max_chunks": 6,
        "chunk_strategy": "fixed",
    },
]
