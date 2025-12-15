# Pfad: /backend/app/models/result.py
"""
FlowAudit Final Result Model

Finale Ergebnisse nach Konfliktlösung zwischen Regel-Engine und LLM.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.feedback import Feedback
    from app.models.llm import LlmRun


class FinalResult(Base):
    """
    Finales Ergebnis einer Dokumentprüfung.

    Kombiniert:
    - Deterministische Regelprüfung
    - LLM-Analyse
    - Benutzer-Overrides

    Berechnet Förderbeträge und Traffic-Light-Status.
    """

    __tablename__ = "final_results"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    llm_run_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("llm_runs.id"), nullable=True
    )

    # Status
    status: Mapped[str] = mapped_column(String(50), default="PENDING")

    # Berechnete Beträge
    computed: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """
    {
        "amounts": {
            "net": {"amount": "100.00", "currency": "EUR"},
            "vat": {"amount": "19.00", "currency": "EUR"},
            "gross": {"amount": "119.00", "currency": "EUR"},
            "eligible_amount": {"amount": "100.00", "currency": "EUR"},
            "funded_amount": {"amount": "70.00", "currency": "EUR"}
        }
    }
    """

    # Feature-Ergebnisse mit Quellen
    fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    """
    [
        {
            "feature_id": "invoice_date",
            "rule_value": "2025-03-01",
            "llm_value": "2025-03-01",
            "user_value": null,
            "final_value": "2025-03-01",
            "source_of_truth": "RULE",
            "conflict_flag": false,
            "conflict_reason": null
        }
    ]
    """

    # Gesamtbewertung
    overall: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """
    {
        "traffic_light": "GREEN",
        "missing_required_features": [],
        "conflicts": []
    }
    """

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="final_results")
    llm_run: Mapped["LlmRun | None"] = relationship("LlmRun")
    feedback_entries: Mapped[list["Feedback"]] = relationship(
        "Feedback", back_populates="final_result"
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        traffic = self.overall.get("traffic_light", "?") if self.overall else "?"
        return f"<FinalResult {self.id[:8]} [{traffic}]>"

    @property
    def traffic_light(self) -> str | None:
        """Traffic-Light-Status."""
        if self.overall:
            return self.overall.get("traffic_light")
        return None

    @property
    def has_conflicts(self) -> bool:
        """Prüft auf Konflikte."""
        if not self.overall:
            return False
        return len(self.overall.get("conflicts", [])) > 0

    @property
    def missing_features(self) -> list[str]:
        """Liste fehlender Pflichtfeatures."""
        if not self.overall:
            return []
        return self.overall.get("missing_required_features", [])

    def get_field_by_id(self, feature_id: str) -> dict | None:
        """
        Gibt Feld-Ergebnis nach Feature-ID zurück.

        Args:
            feature_id: Feature-ID.

        Returns:
            Feld-Dict oder None.
        """
        for field in self.fields:
            if field.get("feature_id") == feature_id:
                return field
        return None

    def get_conflicts(self) -> list[dict]:
        """
        Gibt alle Felder mit Konflikten zurück.

        Returns:
            Liste der Konflikt-Felder.
        """
        return [f for f in self.fields if f.get("conflict_flag")]
