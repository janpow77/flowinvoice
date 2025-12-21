# Pfad: /backend/app/models/solution.py
"""
FlowAudit Solution File Model

Speichert hochgeladene Lösungsdateien für LLM-Training.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class SolutionFile(Base):
    """
    Gespeicherte Lösungsdatei für ein Projekt.

    Enthält:
    - Metadaten der Datei
    - Geparste Einträge
    - Anwendungsstatus
    """

    __tablename__ = "solution_files"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    # Projekt-Zuordnung
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project: Mapped["Project"] = relationship("Project", backref="solution_files")

    # Datei-Metadaten
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)  # JSON, JSONL, CSV
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)

    # Generator-Metadaten
    generator_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Geparste Daten
    entry_count: Mapped[int] = mapped_column(Integer, default=0)
    valid_count: Mapped[int] = mapped_column(Integer, default=0)
    invalid_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    # Einträge als JSON (für spätere Verarbeitung)
    entries: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)

    # Anwendungsstatus
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    applied_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    applied_by: Mapped["User | None"] = relationship("User")

    # Anwendungsstatistik
    applied_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    rag_examples_created: Mapped[int] = mapped_column(Integer, default=0)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<SolutionFile {self.filename} ({self.entry_count} entries)>"


class SolutionMatch(Base):
    """
    Verknüpfung zwischen Lösungsdatei-Eintrag und Dokument.

    Speichert:
    - Welcher Eintrag zu welchem Dokument gehört
    - Anwendungsstatus der Korrekturen
    """

    __tablename__ = "solution_matches"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    # Lösungsdatei-Zuordnung
    solution_file_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("solution_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    solution_file: Mapped["SolutionFile"] = relationship(
        "SolutionFile", backref="matches"
    )

    # Dokument-Zuordnung
    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Match-Details
    solution_position: Mapped[int] = mapped_column(Integer, nullable=False)
    solution_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    match_confidence: Mapped[float] = mapped_column(default=1.0)
    match_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    strategy_used: Mapped[str] = mapped_column(String(50), nullable=True)

    # Lösungsdaten (Kopie vom Eintrag)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    fields: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Anwendungsstatus
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    errors_applied: Mapped[int] = mapped_column(Integer, default=0)
    fields_updated: Mapped[int] = mapped_column(Integer, default=0)
    rag_examples_created: Mapped[int] = mapped_column(Integer, default=0)

    # Notizen
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<SolutionMatch {self.solution_filename} -> {self.document_id}>"
