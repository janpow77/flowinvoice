# Pfad: /backend/app/models/audit.py
"""
FlowAudit Audit Event Model

Audit-Log für alle System-Ereignisse.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditEvent(Base):
    """
    Audit-Ereignis.

    Protokolliert alle wichtigen System-Ereignisse:
    - Uploads
    - Analysen
    - Feedback
    - Training
    - Einstellungsänderungen
    """

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    # Ereignis-Typ
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    """
    Mögliche Typen:
    - DOCUMENT_UPLOADED
    - DOCUMENT_VIEWED
    - DOCUMENT_DOWNLOADED
    - DOCUMENT_DELETED
    - DOCUMENT_PARSED
    - DOCUMENT_PRECHECKED
    - LLM_RUN_STARTED
    - LLM_RUN_COMPLETED
    - LLM_RUN_FAILED
    - FEEDBACK_SUBMITTED
    - RAG_EXAMPLE_CREATED
    - TRAINING_STARTED
    - TRAINING_COMPLETED
    - MODEL_LOADED
    - SETTINGS_CHANGED
    - EXPORT_CREATED
    - GENERATOR_RUN
    - PROJECT_CREATED
    - PROJECT_UPDATED
    - PROJECT_DELETED
    """

    # Entität
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    entity_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True, index=True)

    # Benutzerrolle
    user_role: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Zusätzliche Daten
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Zeitstempel
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<AuditEvent {self.event_type} @ {self.timestamp}>"
