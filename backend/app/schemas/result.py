# Pfad: /backend/app/schemas/result.py
"""
FlowAudit Result Schemas

Schemas für finale Prüfergebnisse.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Money


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
    """Finales Prüfergebnis."""

    model_config = ConfigDict(from_attributes=True)

    final_result_id: str = Field(..., alias="id", description="Ergebnis-ID")
    document_id: str = Field(..., description="Dokument-ID")
    llm_run_id: str | None = Field(default=None, description="LLM-Run-ID")
    status: str = Field(..., description="Status")
    computed: Computed | None = Field(default=None, description="Berechnete Werte")
    fields: list[FieldResult] = Field(default_factory=list, description="Felder")
    overall: Overall | None = Field(default=None, description="Gesamtbewertung")
    created_at: datetime = Field(..., description="Erstellt")
    updated_at: datetime | None = Field(default=None, description="Aktualisiert")


class FinalizeRequest(BaseModel):
    """Finalisierung starten."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Dokument-ID")
    llm_run_id: str | None = Field(default=None, description="LLM-Run-ID")
