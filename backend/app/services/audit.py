# Pfad: /backend/app/services/audit.py
"""
FlowAudit Audit Service

Service für Audit-Trail-Logging aller System-Ereignisse.
Erfüllt DSGVO-Anforderungen für Nachvollziehbarkeit.
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.audit import AuditEvent

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Audit-Event-Typen."""

    # Dokumente
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_VIEWED = "DOCUMENT_VIEWED"
    DOCUMENT_DOWNLOADED = "DOCUMENT_DOWNLOADED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"
    DOCUMENT_PARSED = "DOCUMENT_PARSED"
    DOCUMENT_PRECHECKED = "DOCUMENT_PRECHECKED"

    # LLM
    LLM_RUN_STARTED = "LLM_RUN_STARTED"
    LLM_RUN_COMPLETED = "LLM_RUN_COMPLETED"
    LLM_RUN_FAILED = "LLM_RUN_FAILED"

    # Feedback & Training
    FEEDBACK_SUBMITTED = "FEEDBACK_SUBMITTED"
    RAG_EXAMPLE_CREATED = "RAG_EXAMPLE_CREATED"
    TRAINING_STARTED = "TRAINING_STARTED"
    TRAINING_COMPLETED = "TRAINING_COMPLETED"

    # System
    MODEL_LOADED = "MODEL_LOADED"
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    EXPORT_CREATED = "EXPORT_CREATED"
    GENERATOR_RUN = "GENERATOR_RUN"

    # Projekte
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    PROJECT_DELETED = "PROJECT_DELETED"


class AuditService:
    """
    Service für Audit-Trail-Logging.

    Verwendung:
        audit = AuditService()
        await audit.log(
            AuditEventType.DOCUMENT_VIEWED,
            entity_type="document",
            entity_id="123-456",
            data={"filename": "rechnung.pdf"}
        )
    """

    async def log(
        self,
        event_type: AuditEventType,
        entity_type: str | None = None,
        entity_id: str | None = None,
        user_role: str | None = None,
        data: dict[str, Any] | None = None,
        session: AsyncSession | None = None,
    ) -> AuditEvent:
        """
        Loggt ein Audit-Event.

        Args:
            event_type: Art des Events
            entity_type: Typ der Entität (document, project, etc.)
            entity_id: ID der Entität
            user_role: Rolle des Benutzers (optional)
            data: Zusätzliche Daten
            session: Optionale DB-Session (falls bereits vorhanden)

        Returns:
            Erstelltes AuditEvent
        """
        event = AuditEvent(
            event_type=event_type.value,
            entity_type=entity_type,
            entity_id=entity_id,
            user_role=user_role,
            data=data,
            timestamp=datetime.now(timezone.utc),
        )

        if session:
            session.add(event)
            await session.flush()
        else:
            async with async_session_maker() as new_session:
                new_session.add(event)
                await new_session.commit()

        logger.debug(
            f"Audit: {event_type.value} - {entity_type}:{entity_id}"
        )

        return event

    async def log_document_access(
        self,
        document_id: str,
        filename: str,
        action: str = "viewed",
        session: AsyncSession | None = None,
    ) -> AuditEvent:
        """
        Convenience-Methode für Dokument-Zugriffe.

        Args:
            document_id: Dokument-ID
            filename: Dateiname
            action: Art des Zugriffs (viewed, downloaded, deleted)
            session: DB-Session

        Returns:
            AuditEvent
        """
        event_map = {
            "viewed": AuditEventType.DOCUMENT_VIEWED,
            "downloaded": AuditEventType.DOCUMENT_DOWNLOADED,
            "deleted": AuditEventType.DOCUMENT_DELETED,
            "uploaded": AuditEventType.DOCUMENT_UPLOADED,
        }

        return await self.log(
            event_type=event_map.get(action, AuditEventType.DOCUMENT_VIEWED),
            entity_type="document",
            entity_id=document_id,
            data={"filename": filename, "action": action},
            session=session,
        )

    async def log_llm_analysis(
        self,
        document_id: str,
        provider: str,
        model: str,
        success: bool,
        duration_ms: int | None = None,
        error: str | None = None,
        session: AsyncSession | None = None,
    ) -> AuditEvent:
        """
        Loggt LLM-Analyse.

        Args:
            document_id: Dokument-ID
            provider: LLM-Provider
            model: Verwendetes Modell
            success: Erfolg ja/nein
            duration_ms: Dauer in Millisekunden
            error: Fehlermeldung (falls vorhanden)
            session: DB-Session

        Returns:
            AuditEvent
        """
        event_type = (
            AuditEventType.LLM_RUN_COMPLETED
            if success
            else AuditEventType.LLM_RUN_FAILED
        )

        return await self.log(
            event_type=event_type,
            entity_type="document",
            entity_id=document_id,
            data={
                "provider": provider,
                "model": model,
                "success": success,
                "duration_ms": duration_ms,
                "error": error,
            },
            session=session,
        )


# Globale Instanz
_audit_service: AuditService | None = None


def get_audit_service() -> AuditService:
    """Gibt Audit-Service-Singleton zurück."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
