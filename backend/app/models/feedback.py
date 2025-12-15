# Pfad: /backend/app/models/feedback.py
"""
FlowAudit Feedback and RAG Example Models

Human-in-the-loop Feedback und RAG-Beispiele für Few-Shot-Learning.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import FeedbackRating

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.project import Project
    from app.models.result import FinalResult


class Feedback(Base):
    """
    Benutzer-Feedback zu einem Prüfergebnis.

    Kann:
    - Ergebnis akzeptieren
    - Einzelne Features korrigieren
    - Kommentar hinzufügen
    """

    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    final_result_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("final_results.id"), nullable=True
    )

    # Bewertung
    rating: Mapped[FeedbackRating] = mapped_column(Enum(FeedbackRating), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Korrekturen
    overrides: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    """
    [
        {
            "feature_id": "vat_amount",
            "user_value": "19.00",
            "note": "OCR misread 18.90"
        }
    ]
    """

    # Akzeptanz
    accept_result: Mapped[bool] = mapped_column(Boolean, default=False)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="feedback_entries")
    final_result: Mapped["FinalResult | None"] = relationship(
        "FinalResult", back_populates="feedback_entries"
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<Feedback {self.id[:8]} [{self.rating.value}]>"

    @property
    def has_overrides(self) -> bool:
        """Prüft auf Korrekturen."""
        return len(self.overrides) > 0

    @property
    def override_count(self) -> int:
        """Anzahl der Korrekturen."""
        return len(self.overrides)

    def get_override(self, feature_id: str) -> dict[str, Any] | None:
        """
        Gibt Override für Feature zurück.

        Args:
            feature_id: Feature-ID.

        Returns:
            Override-Dict oder None.
        """
        for override in self.overrides:
            if override.get("feature_id") == feature_id:
                return override
        return None


class RagExample(Base):
    """
    RAG-Beispiel für Few-Shot-Learning.

    Wird aus bestätigtem Feedback erzeugt und in ChromaDB gespeichert.
    """

    __tablename__ = "rag_examples"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    # Quellen
    document_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("documents.id"), nullable=True
    )
    feedback_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("feedback.id"), nullable=True
    )
    project_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id"), nullable=True
    )

    # Metadaten
    ruleset_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    feature_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    correction_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Inhalt
    original_text_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_llm_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    corrected_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Embedding (für ChromaDB-Sync)
    embedding_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Embedding-Vektor wird in ChromaDB gespeichert, nicht hier

    # Nutzungsstatistik
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    document: Mapped["Document | None"] = relationship("Document")
    feedback: Mapped["Feedback | None"] = relationship("Feedback")
    project: Mapped["Project | None"] = relationship("Project")

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<RagExample {self.id[:8]} [{self.feature_id}]>"

    def increment_usage(self) -> None:
        """Erhöht Nutzungszähler."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
