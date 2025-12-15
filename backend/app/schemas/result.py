# Pfad: /backend/app/schemas/result.py
"""
FlowAudit Result Schemas

Schemas für finale Prüfergebnisse inkl. Versionierungs-Metadaten.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AnalysisStatus, ConflictStatus
from app.schemas.common import Money


class AnalysisMetadata(BaseModel):
    """
    Pflicht-Metadaten für Nachvollziehbarkeit und Reproduzierbarkeit.

    Ergebnisse ohne vollständige Metadaten sind als INVALID zu markieren.
    """

    model_config = ConfigDict(from_attributes=True)

    # Dokument-Fingerprint
    document_fingerprint: str = Field(
        ..., description="SHA-256 Hash des Dokuments"
    )

    # Ruleset-Versionierung
    ruleset_id: str = Field(
        ..., description="Regelwerk-ID (z.B. DE_USTG)"
    )
    ruleset_version: str = Field(
        ..., description="Regelwerk-Version (z.B. 2024.1)"
    )

    # Prompt-Versionierung
    prompt_version: str = Field(
        default="1.0.0", description="Version des LLM-Prompts"
    )

    # Model-Info
    model_id: str = Field(
        ..., description="LLM-Model-ID (z.B. gpt-4-turbo)"
    )
    model_provider: str = Field(
        default="", description="LLM-Provider (z.B. OPENAI)"
    )

    # Zeitstempel
    analysis_timestamp: str = Field(
        ..., description="Zeitstempel der Analyse (ISO 8601)"
    )

    # System-Version
    system_version: str = Field(
        default="1.0.0", description="FlowAudit System-Version"
    )

    # Optional: Zusätzliche Metadaten
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Zusätzliche Metadaten"
    )

    @classmethod
    def create_now(
        cls,
        document_fingerprint: str,
        ruleset_id: str,
        ruleset_version: str,
        model_id: str,
        model_provider: str = "",
        prompt_version: str = "1.0.0",
        system_version: str = "1.0.0",
    ) -> "AnalysisMetadata":
        """Factory-Methode für neue Metadaten."""
        return cls(
            document_fingerprint=document_fingerprint,
            ruleset_id=ruleset_id,
            ruleset_version=ruleset_version,
            model_id=model_id,
            model_provider=model_provider,
            prompt_version=prompt_version,
            analysis_timestamp=datetime.utcnow().isoformat() + "Z",
            system_version=system_version,
        )


class UnclearStatus(BaseModel):
    """
    UNCLEAR-Status mit Begründungspflicht.

    Kriterien für UNCLEAR:
    1. Relevante Informationen fehlen vollständig
    2. Vorhandene Informationen sind mehrdeutig
    3. Mehrere fachlich plausible Interpretationen möglich
    """

    model_config = ConfigDict(from_attributes=True)

    is_unclear: bool = Field(
        default=False, description="UNCLEAR-Status aktiv"
    )
    unclear_reason: Optional[str] = Field(
        default=None, description="Beschreibung der Unklarheit"
    )
    required_clarification: Optional[str] = Field(
        default=None, description="Benötigte Information zur Klärung"
    )
    affected_fields: list[str] = Field(
        default_factory=list, description="Betroffene Felder"
    )


class ComputedAmounts(BaseModel):
    """Berechnete Beträge."""

    model_config = ConfigDict(from_attributes=True)

    net: Money = Field(..., description="Nettobetrag")
    vat: Money = Field(..., description="MwSt-Betrag")
    gross: Money = Field(..., description="Bruttobetrag")
    eligible_amount: Money | None = Field(
        default=None, description="Förderfähiger Betrag"
    )
    funded_amount: Money | None = Field(default=None, description="Förderbetrag")


class Computed(BaseModel):
    """Berechnete Werte."""

    model_config = ConfigDict(from_attributes=True)

    amounts: ComputedAmounts = Field(..., description="Beträge")


class FieldResult(BaseModel):
    """Feld-Ergebnis mit Quellen."""

    model_config = ConfigDict(from_attributes=True)

    feature_id: str = Field(..., description="Feature-ID")
    rule_value: Any = Field(default=None, description="Regel-Wert")
    llm_value: Any = Field(default=None, description="LLM-Wert")
    user_value: Any = Field(default=None, description="Benutzer-Wert")
    final_value: Any = Field(default=None, description="Finaler Wert")
    source_of_truth: str = Field(..., description="RULE | LLM | USER")
    conflict_flag: bool = Field(default=False, description="Konflikt vorhanden")
    conflict_reason: str | None = Field(default=None, description="Konfliktgrund")


class Conflict(BaseModel):
    """Konflikt-Detail."""

    model_config = ConfigDict(from_attributes=True)

    feature_id: str = Field(..., description="Feature-ID")
    rule_value: Any = Field(default=None, description="Regel-Wert")
    llm_value: Any = Field(default=None, description="LLM-Wert")
    reason: str = Field(..., description="Grund")


class Overall(BaseModel):
    """Gesamtbewertung."""

    model_config = ConfigDict(from_attributes=True)

    traffic_light: str = Field(..., description="GREEN | YELLOW | RED")
    missing_required_features: list[str] = Field(
        default_factory=list, description="Fehlende Pflichtfelder"
    )
    conflicts: list[Conflict] = Field(default_factory=list, description="Konflikte")
    score: int | None = Field(default=None, description="Qualitätsscore (0-100)")


class FinalResultResponse(BaseModel):
    """Finales Prüfergebnis mit vollständigen Metadaten."""

    model_config = ConfigDict(from_attributes=True)

    final_result_id: str = Field(..., alias="id", description="Ergebnis-ID")
    document_id: str = Field(..., description="Dokument-ID")
    llm_run_id: str | None = Field(default=None, description="LLM-Run-ID")
    status: str = Field(..., description="Status")

    # Analysestatus (inkl. Fehlerzustände)
    analysis_status: AnalysisStatus = Field(
        default=AnalysisStatus.COMPLETED,
        description="Detaillierter Analysestatus",
    )

    # Berechnete Werte
    computed: Computed | None = Field(default=None, description="Berechnete Werte")
    fields: list[FieldResult] = Field(default_factory=list, description="Felder")
    overall: Overall | None = Field(default=None, description="Gesamtbewertung")

    # Versionierungs-Metadaten (Pflicht für Reproduzierbarkeit)
    metadata: AnalysisMetadata | None = Field(
        default=None,
        description="Analyse-Metadaten für Nachvollziehbarkeit",
    )

    # UNCLEAR-Status
    unclear_status: UnclearStatus | None = Field(
        default=None,
        description="UNCLEAR-Status mit Begründung",
    )

    # Zeitstempel
    created_at: datetime = Field(..., description="Erstellt")
    updated_at: datetime | None = Field(default=None, description="Aktualisiert")

    def is_valid(self) -> bool:
        """Prüft ob Ergebnis valide ist (alle Pflicht-Metadaten vorhanden)."""
        if not self.metadata:
            return False
        return bool(
            self.metadata.document_fingerprint
            and self.metadata.ruleset_id
            and self.metadata.model_id
        )


class FinalizeRequest(BaseModel):
    """Finalisierung starten."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Dokument-ID")
    llm_run_id: str | None = Field(default=None, description="LLM-Run-ID")
