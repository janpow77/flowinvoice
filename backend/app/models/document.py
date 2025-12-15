# Pfad: /backend/app/models/document.py
"""
FlowAudit Document Models

Dokumente (Rechnungen) und zugehörige Parse/Precheck-Runs.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import DocumentStatus

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.llm import LlmRun, PreparePayload
    from app.models.project import Project
    from app.models.result import FinalResult


class Document(Base):
    """
    Hochgeladenes Dokument (Rechnung).

    Wird durch den Workflow verarbeitet:
    UPLOADED -> PARSING -> PARSED -> PRECHECKED -> PREPARED -> LLM_RUNNING -> LLM_DONE -> REVIEW_PENDING -> ACCEPTED/REJECTED
    """

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    # Projekt-Zuordnung
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    # Datei-Informationen
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.UPLOADED, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Ruleset
    ruleset_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ruleset_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ui_language: Mapped[str] = mapped_column(String(5), default="de")

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="documents")
    parse_runs: Mapped[list["ParseRun"]] = relationship(
        "ParseRun", back_populates="document", cascade="all, delete-orphan"
    )
    precheck_runs: Mapped[list["PrecheckRun"]] = relationship(
        "PrecheckRun", back_populates="document", cascade="all, delete-orphan"
    )
    payloads: Mapped[list["PreparePayload"]] = relationship(
        "PreparePayload", back_populates="document", cascade="all, delete-orphan"
    )
    llm_runs: Mapped[list["LlmRun"]] = relationship(
        "LlmRun", back_populates="document", cascade="all, delete-orphan"
    )
    final_results: Mapped[list["FinalResult"]] = relationship(
        "FinalResult", back_populates="document", cascade="all, delete-orphan"
    )
    feedback_entries: Mapped[list["Feedback"]] = relationship(
        "Feedback", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<Document {self.original_filename} [{self.status.value}]>"

    @property
    def latest_parse_run(self) -> "ParseRun | None":
        """Neuester Parse-Run."""
        if not self.parse_runs:
            return None
        return max(self.parse_runs, key=lambda r: r.created_at)

    @property
    def latest_precheck_run(self) -> "PrecheckRun | None":
        """Neuester Precheck-Run."""
        if not self.precheck_runs:
            return None
        return max(self.precheck_runs, key=lambda r: r.created_at)

    @property
    def latest_payload(self) -> "PreparePayload | None":
        """Neuestes PreparePayload."""
        if not self.payloads:
            return None
        return max(self.payloads, key=lambda p: p.created_at)

    @property
    def latest_llm_run(self) -> "LlmRun | None":
        """Neuester LLM-Run."""
        if not self.llm_runs:
            return None
        return max(self.llm_runs, key=lambda r: r.created_at)


class ParseRun(Base):
    """
    Parse-Durchlauf für ein Dokument.

    Extrahiert Text und strukturierte Daten aus PDF.
    """

    __tablename__ = "parse_runs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )

    # Parse-Engine
    engine: Mapped[str] = mapped_column(String(50), default="HYBRID")
    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    # Ergebnisse
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    pages: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    extracted: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timing
    timings_ms: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="parse_runs")

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<ParseRun {self.id[:8]} [{self.status}]>"


class PrecheckRun(Base):
    """
    Precheck-Durchlauf (deterministische Regelprüfung).

    Prüft ohne KI: Datum, Beträge, Format, etc.
    """

    __tablename__ = "precheck_runs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    checks: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="precheck_runs")

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<PrecheckRun {self.id[:8]} [{self.status}]>"

    def get_check_by_id(self, check_id: str) -> dict | None:
        """
        Findet einen Check nach ID.

        Args:
            check_id: Check-ID.

        Returns:
            Check-Dict oder None.
        """
        for check in self.checks:
            if check.get("check_id") == check_id:
                return check
        return None
