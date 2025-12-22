"""
BatchJob Model

Model für die Verwaltung von Batch-Jobs für Massenverarbeitung.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import BatchJobStatus


class BatchJob(Base):
    """
    Batch-Job für Massenverarbeitung von Dokumenten.

    Unterstützte Job-Typen:
    - BATCH_GENERATE: Test-Dokumente generieren
    - BATCH_ANALYZE: Mehrere Dokumente analysieren
    - BATCH_VALIDATE: Mehrere Dokumente validieren
    - BATCH_EXPORT: Ergebnisse exportieren
    - SOLUTION_APPLY: Lösungsdatei anwenden
    - RAG_REBUILD: RAG-Index neu aufbauen
    """

    __tablename__ = "batch_jobs"

    # Primary Key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Job-Typ
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Zuordnung zu Projekt (optional)
    project_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=BatchJobStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    # Ersteller
    created_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Job-Parameter
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Fortschritt
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    processed_items: Mapped[int] = mapped_column(Integer, default=0)
    successful_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    skipped_items: Mapped[int] = mapped_column(Integer, default=0)

    # Fortschritt in Prozent
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)

    # Ergebnisse und Fehler
    results: Mapped[dict] = mapped_column(JSONB, default=dict)
    errors: Mapped[list] = mapped_column(JSONB, default=list)
    warnings: Mapped[list] = mapped_column(JSONB, default=list)

    # Status-Nachricht
    status_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Celery Task ID
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Geplante Ausführung (für periodische Jobs)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_cron: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Priorität (höher = wichtiger)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Job-Verkettung (wartet auf anderen Job)
    depends_on_job_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("batch_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Wiederholungseinstellungen
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    project = relationship("Project", back_populates="batch_jobs")

    def __repr__(self) -> str:
        return f"<BatchJob {self.id} type={self.job_type} status={self.status}>"

    @property
    def is_running(self) -> bool:
        """Prüft, ob der Job gerade läuft."""
        return self.status == BatchJobStatus.RUNNING.value

    @property
    def is_completed(self) -> bool:
        """Prüft, ob der Job abgeschlossen ist."""
        return self.status in [
            BatchJobStatus.COMPLETED.value,
            BatchJobStatus.FAILED.value,
            BatchJobStatus.CANCELLED.value,
        ]

    @property
    def duration_seconds(self) -> Optional[float]:
        """Berechnet die Laufzeit in Sekunden."""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    def update_progress(
        self,
        processed: int,
        successful: int = 0,
        failed: int = 0,
        skipped: int = 0,
        message: Optional[str] = None,
    ) -> None:
        """Aktualisiert den Fortschritt des Jobs."""
        self.processed_items = processed
        self.successful_items = successful
        self.failed_items = failed
        self.skipped_items = skipped

        if self.total_items > 0:
            self.progress_percent = (processed / self.total_items) * 100

        if message:
            self.status_message = message

    def mark_started(self) -> None:
        """Markiert den Job als gestartet."""
        self.status = BatchJobStatus.RUNNING.value
        self.started_at = datetime.utcnow()

    def mark_completed(self, results: Optional[dict] = None) -> None:
        """Markiert den Job als abgeschlossen."""
        self.status = BatchJobStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.progress_percent = 100.0
        if results:
            self.results = results

    def mark_failed(self, error: str, errors: Optional[list] = None) -> None:
        """Markiert den Job als fehlgeschlagen."""
        self.status = BatchJobStatus.FAILED.value
        self.completed_at = datetime.utcnow()
        self.status_message = error
        if errors:
            self.errors = errors

    def mark_cancelled(self) -> None:
        """Markiert den Job als abgebrochen."""
        self.status = BatchJobStatus.CANCELLED.value
        self.completed_at = datetime.utcnow()
        self.status_message = "Job wurde abgebrochen"

    def add_error(self, error: str, item_id: Optional[str] = None) -> None:
        """Fügt einen Fehler zur Fehlerliste hinzu."""
        self.errors = self.errors or []
        self.errors.append({
            "message": error,
            "item_id": item_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def add_warning(self, warning: str, item_id: Optional[str] = None) -> None:
        """Fügt eine Warnung zur Warnungsliste hinzu."""
        self.warnings = self.warnings or []
        self.warnings.append({
            "message": warning,
            "item_id": item_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
