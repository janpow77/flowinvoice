# Pfad: /backend/app/models/export.py
"""
FlowAudit Export and Generator Models

Export-Jobs und Generator-Jobs.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class ExportJob(Base):
    """
    Export-Job.

    Exportiert Projekt-Ergebnisse in verschiedene Formate (XLSX, CSV, JSON).
    """

    __tablename__ = "export_jobs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    project_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id"), nullable=True
    )

    # Format
    format: Mapped[str] = mapped_column(String(20), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    # Ausgabedatei
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Optionen
    options: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    """
    {
        "only_status": ["ACCEPTED"],
        "include_payloads": false,
        "include_llm_responses": false
    }
    """

    # Fehler
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project: Mapped["Project | None"] = relationship("Project")

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<ExportJob {self.id[:8]} [{self.format}]>"


class GeneratorJob(Base):
    """
    Generator-Job.

    Erzeugt Dummy-Rechnungen für Seminarbetrieb.
    """

    __tablename__ = "generator_jobs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    project_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id"), nullable=True
    )

    # Ruleset und Sprache
    ruleset_id: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(5), default="de")

    # Anzahl
    count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Aktive Templates
    templates_enabled: Mapped[list[str]] = mapped_column(ARRAY(String(50)), nullable=False)

    # Generator-Einstellungen
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    """
    {
        "error_rate_total": 5.0,
        "severity": 2,
        "per_feature_error_rates": {
            "supplier_tax_or_vat_id": 3.0
        },
        "date_format_profiles": ["DD.MM.YYYY"],
        "alias_noise_probability": 10.0
    }
    """

    # Status
    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    # Ausgabe
    output_dir: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    solutions_file: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    generated_files: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)

    # Fehler
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project: Mapped["Project | None"] = relationship("Project")

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<GeneratorJob {self.id[:8]} [{self.count} invoices]>"
