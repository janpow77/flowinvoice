# Pfad: /backend/app/models/result.py
"""
FlowAudit Final Result Model

Finale Ergebnisse nach Konfliktlösung zwischen Regel-Engine und LLM.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import Provider

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
    computed: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
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
    fields: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
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
    overall: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
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
        features: list[str] = self.overall.get("missing_required_features", [])
        return features

    def get_field_by_id(self, feature_id: str) -> dict[str, Any] | None:
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

    def get_conflicts(self) -> list[dict[str, Any]]:
        """
        Gibt alle Felder mit Konflikten zurück.

        Returns:
            Liste der Konflikt-Felder.
        """
        return [f for f in self.fields if f.get("conflict_flag")]


class AnalysisResult(Base):
    """
    LLM-Analyseergebnis für ein Dokument.

    Speichert das Ergebnis der KI-Analyse mit allen relevanten Metriken.
    """

    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )

    # Provider und Modell
    provider: Mapped[Provider] = mapped_column(Enum(Provider), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)

    # Prüfergebnisse
    semantic_check: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    economic_check: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    beneficiary_match: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    warnings: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)

    # Gesamtbewertung
    overall_assessment: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Token-Statistiken
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<AnalysisResult {self.id[:8]} [{self.overall_assessment}]>"
