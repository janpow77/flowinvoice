# Pfad: /backend/app/models/ruleset_sample.py
"""
FlowAudit Ruleset Sample Model

Musterdokumente für Regelwerke (Training/RAG).
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SampleStatus


class RulesetSample(Base):
    """
    Musterdokument für ein Regelwerk.

    Samples werden hochgeladen, automatisch geparst und dann
    von einem Admin reviewed. Nach Approval werden sie als
    RAG-Trainingsbeispiele verwendet.
    """

    __tablename__ = "ruleset_samples"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    # Ruleset-Referenz
    ruleset_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    ruleset_version: Mapped[str] = mapped_column(String(20), nullable=False)

    # Datei-Informationen
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")

    # Beschreibung
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[SampleStatus] = mapped_column(
        String(20), default=SampleStatus.UPLOADED, nullable=False, index=True
    )

    # Extrahierte Daten (nach Parsing)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Ground Truth (nach Review)
    ground_truth: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Parsing-Fehler (falls vorhanden)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # RAG-Referenz (nach Approval)
    rag_example_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Approved by (User-ID)
    approved_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<RulesetSample {self.filename} ({self.status})>"

    @property
    def is_pending_review(self) -> bool:
        """Prüft ob Sample auf Review wartet."""
        return self.status == SampleStatus.PENDING_REVIEW

    @property
    def is_approved(self) -> bool:
        """Prüft ob Sample approved ist."""
        return self.status == SampleStatus.APPROVED

    @property
    def has_ground_truth(self) -> bool:
        """Prüft ob Ground Truth vorhanden ist."""
        return self.ground_truth is not None and len(self.ground_truth) > 0
