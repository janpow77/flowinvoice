# Pfad: /backend/app/schemas/llm.py
"""
FlowAudit LLM Schemas

Schemas für PreparePayload und LLM-Runs.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Provider


class PreparePayloadResponse(BaseModel):
    """PreparePayload Response (INPUT-JSON an KI)."""

    model_config = ConfigDict(from_attributes=True)

    payload_id: str = Field(..., alias="id", description="Payload-ID")
    document_id: str = Field(..., description="Dokument-ID")
    schema_version: str = Field(..., description="Schema-Version")
    ruleset: dict[str, Any] = Field(..., description="Ruleset-Info")
    ui_language: str = Field(..., description="UI-Sprache")
    project_context: dict[str, Any] | None = Field(
        default=None, description="Projekt-Kontext"
    )
    parsing_summary: dict[str, Any] | None = Field(
        default=None, description="Parse-Zusammenfassung"
    )
    deterministic_precheck_results: dict[str, Any] | None = Field(
        default=None, description="Precheck-Ergebnisse"
    )
    features: list[dict[str, Any]] = Field(..., description="Zu prüfende Features")
    extracted_text: str | None = Field(default=None, description="Extrahierter Text")
    required_output_schema: dict[str, Any] | None = Field(
        default=None, description="Output-Schema"
    )
    rag_context: dict[str, Any] | None = Field(default=None, description="RAG-Kontext")
    created_at: datetime = Field(..., description="Erstellt")


class LlmRunCreate(BaseModel):
    """LLM-Run starten."""

    model_config = ConfigDict(from_attributes=True)

    payload_id: str | None = Field(default=None, description="Payload-ID")
    provider_override: Provider | None = Field(default=None, description="Provider-Override")
    model_override: str | None = Field(default=None, description="Modell-Override")


class FeatureEvidence(BaseModel):
    """Evidenz für Feature-Extraktion."""

    model_config = ConfigDict(from_attributes=True)

    page: int = Field(..., description="Seite")
    x0: float = Field(..., description="X0")
    y0: float = Field(..., description="Y0")
    x1: float = Field(..., description="X1")
    y1: float = Field(..., description="Y1")
    confidence: float = Field(default=1.0, description="Konfidenz")
    text: str | None = Field(default=None, description="Text")


class FeatureResult(BaseModel):
    """Feature-Ergebnis aus LLM-Response."""

    model_config = ConfigDict(from_attributes=True)

    feature_id: str = Field(..., description="Feature-ID")
    status: str = Field(..., description="PRESENT | MISSING | UNCLEAR")
    extracted_value: Any = Field(default=None, description="Extrahierter Wert")
    confidence: int = Field(default=0, ge=0, le=100, description="Konfidenz (0-100)")
    rationale: str | None = Field(default=None, description="Begründung")
    evidence: list[FeatureEvidence] = Field(
        default_factory=list, description="Evidenz"
    )


class LocationMatchResult(BaseModel):
    """Standort-Übereinstimmungsergebnis."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="MATCH | PARTIAL | MISMATCH | UNCLEAR")
    confidence: int = Field(default=0, description="Konfidenz (0-100)")
    invoice_value: str | None = Field(default=None, description="Wert aus Rechnung")
    project_value: str | None = Field(default=None, description="Wert aus Projekt")
    note: str | None = Field(default=None, description="Anmerkung")


class LocationFit(BaseModel):
    """Standort-Validierung."""

    model_config = ConfigDict(from_attributes=True)

    customer_matches_beneficiary: LocationMatchResult = Field(
        ..., description="Rechnungsempfänger ↔ Begünstigter"
    )
    service_location_matches_implementation: LocationMatchResult = Field(
        ..., description="Leistungsort ↔ Durchführungsort"
    )
    service_location_matches_beneficiary: LocationMatchResult = Field(
        ..., description="Leistungsort ↔ Sitz Begünstigter"
    )
    overall_location_plausibility: str = Field(
        ..., description="PLAUSIBLE | UNCLEAR | IMPLAUSIBLE"
    )
    rationale: str | None = Field(default=None, description="Begründung")


class SemanticProjectFit(BaseModel):
    """Semantischer Projektbezug."""

    model_config = ConfigDict(from_attributes=True)

    relation_level: str = Field(..., description="YES | PARTIAL | UNCLEAR | NO")
    reasons: list[str] = Field(default_factory=list, description="Gründe")
    mapped_cost_category: str | None = Field(default=None, description="Kostenart")
    time_plausible: bool = Field(default=True, description="Zeitlich plausibel")
    beneficiary_plausible: bool = Field(
        default=True, description="Begünstigter plausibel"
    )
    location_fit: LocationFit | None = Field(
        default=None, description="Standort-Validierung"
    )


class StructuredResponse(BaseModel):
    """Strukturierte LLM-Response."""

    model_config = ConfigDict(from_attributes=True)

    features: list[FeatureResult] = Field(..., description="Feature-Ergebnisse")
    semantic_project_fit: SemanticProjectFit | None = Field(
        default=None, description="Projektbezug"
    )


class TokenUsage(BaseModel):
    """Token-Verbrauch."""

    model_config = ConfigDict(from_attributes=True)

    input: int = Field(..., description="Input-Tokens")
    output: int = Field(..., description="Output-Tokens")


class LlmRunResponse(BaseModel):
    """LLM-Run Response."""

    model_config = ConfigDict(from_attributes=True)

    llm_run_id: str = Field(..., alias="id", description="LLM-Run-ID")
    document_id: str = Field(..., description="Dokument-ID")
    payload_id: str | None = Field(default=None, description="Payload-ID")
    provider: Provider = Field(..., description="Provider")
    model_name: str = Field(..., description="Modellname")
    status: str = Field(..., description="Status")
    timings_ms: dict[str, int] | None = Field(default=None, description="Timing")
    token_usage: TokenUsage | None = Field(default=None, description="Token-Verbrauch")
    raw_response_text: str | None = Field(default=None, description="Roh-Response")
    structured_response: StructuredResponse | None = Field(
        default=None, description="Strukturierte Response"
    )
    error_message: str | None = Field(default=None, description="Fehlermeldung")
    created_at: datetime = Field(..., description="Erstellt")
    completed_at: datetime | None = Field(default=None, description="Abgeschlossen")


class LlmRunLogItem(BaseModel):
    """Log-Eintrag."""

    model_config = ConfigDict(from_attributes=True)

    ts: datetime = Field(..., alias="timestamp", description="Zeitstempel")
    level: str = Field(..., description="Log-Level")
    msg: str = Field(..., alias="message", description="Nachricht")
    data: dict[str, Any] | None = Field(default=None, description="Daten")


class LlmRunLogResponse(BaseModel):
    """LLM-Run Logs Response."""

    model_config = ConfigDict(from_attributes=True)

    llm_run_id: str = Field(..., description="LLM-Run-ID")
    events: list[LlmRunLogItem] = Field(default_factory=list, description="Log-Events")
