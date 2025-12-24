# Pfad: /backend/app/schemas/ruleset_checker.py
"""
FlowAudit Ruleset Checker Schemas

Schemas für Prüfmodul-Konfiguration pro Regelwerk.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RiskCheckerConfig(BaseModel):
    """Konfiguration für Risk Checker."""

    model_config = ConfigDict(from_attributes=True)

    enabled: bool = Field(default=True, description="Risk Checker aktiviert")
    severity_threshold: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        default="MEDIUM", description="Mindest-Schweregrad für Warnungen"
    )
    check_self_invoice: bool = Field(
        default=True, description="Prüfung auf Eigenrechnungen"
    )
    check_duplicate_invoice: bool = Field(
        default=True, description="Prüfung auf Duplikate"
    )
    check_round_amounts: bool = Field(
        default=True, description="Prüfung auf auffällig runde Beträge"
    )
    check_weekend_dates: bool = Field(
        default=True, description="Prüfung auf Wochenenddaten"
    )
    round_amount_threshold: int = Field(
        default=1000, description="Schwellwert für runde Beträge (EUR)"
    )


class SemanticCheckerConfig(BaseModel):
    """Konfiguration für Semantic Checker."""

    model_config = ConfigDict(from_attributes=True)

    enabled: bool = Field(default=True, description="Semantic Checker aktiviert")
    severity_threshold: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        default="MEDIUM", description="Mindest-Schweregrad für Warnungen"
    )
    check_project_relevance: bool = Field(
        default=True, description="Prüfung auf Projektrelevanz"
    )
    check_description_quality: bool = Field(
        default=True, description="Prüfung der Leistungsbeschreibung"
    )
    min_relevance_score: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Mindest-Relevanz-Score (0-1)"
    )
    use_rag_context: bool = Field(
        default=True, description="RAG-Kontext für Prüfung verwenden"
    )


class EconomicCheckerConfig(BaseModel):
    """Konfiguration für Economic Checker."""

    model_config = ConfigDict(from_attributes=True)

    enabled: bool = Field(default=True, description="Economic Checker aktiviert")
    severity_threshold: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        default="LOW", description="Mindest-Schweregrad für Warnungen"
    )
    check_budget_limits: bool = Field(
        default=True, description="Prüfung auf Budgetgrenzen"
    )
    check_unit_prices: bool = Field(
        default=True, description="Prüfung auf marktübliche Preise"
    )
    check_funding_rate: bool = Field(
        default=True, description="Prüfung der Förderquote"
    )
    max_deviation_percent: int = Field(
        default=20, ge=0, le=100, description="Max. Abweichung in Prozent"
    )


class LegalCheckerConfig(BaseModel):
    """Konfiguration für Legal Checker (Legal Retrieval / Normenhierarchie)."""

    model_config = ConfigDict(from_attributes=True)

    enabled: bool = Field(
        default=False,
        description="Legal Checker aktiviert - bindet Rechtstexte in die Analyse ein"
    )
    funding_period: Literal["2014-2020", "2021-2027"] = Field(
        default="2021-2027", description="EU-Förderperiode für Rechtstexte"
    )
    max_results: int = Field(
        default=5, ge=1, le=20, description="Max. Anzahl Rechtstexte pro Analyse"
    )
    min_relevance_score: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Mindest-Relevanz für Rechtstexte"
    )
    use_hierarchy_weighting: bool = Field(
        default=True,
        description="Normenhierarchie-Gewichtung (EU-VO > Nat. Recht > Guidance)"
    )
    include_definitions: bool = Field(
        default=True, description="Legaldefinitionen in Kontext einbeziehen"
    )


class RulesetCheckerSettingsResponse(BaseModel):
    """Response für Checker-Einstellungen eines Regelwerks."""

    model_config = ConfigDict(from_attributes=True)

    ruleset_id: str = Field(..., description="Ruleset-ID")
    risk_checker: RiskCheckerConfig = Field(..., description="Risk Checker Konfiguration")
    semantic_checker: SemanticCheckerConfig = Field(
        ..., description="Semantic Checker Konfiguration"
    )
    economic_checker: EconomicCheckerConfig = Field(
        ..., description="Economic Checker Konfiguration"
    )
    legal_checker: LegalCheckerConfig = Field(
        ..., description="Legal Checker Konfiguration (Legal Retrieval)"
    )
    created_at: datetime | None = Field(default=None, description="Erstellungszeitpunkt")
    updated_at: datetime | None = Field(default=None, description="Aktualisierung")


class RulesetCheckerSettingsUpdate(BaseModel):
    """Update für Checker-Einstellungen."""

    model_config = ConfigDict(from_attributes=True)

    risk_checker: RiskCheckerConfig | None = Field(
        default=None, description="Risk Checker Konfiguration"
    )
    semantic_checker: SemanticCheckerConfig | None = Field(
        default=None, description="Semantic Checker Konfiguration"
    )
    economic_checker: EconomicCheckerConfig | None = Field(
        default=None, description="Economic Checker Konfiguration"
    )
    legal_checker: LegalCheckerConfig | None = Field(
        default=None, description="Legal Checker Konfiguration (Legal Retrieval)"
    )


# Default-Konfigurationen
DEFAULT_RISK_CHECKER = RiskCheckerConfig()
DEFAULT_SEMANTIC_CHECKER = SemanticCheckerConfig()
DEFAULT_ECONOMIC_CHECKER = EconomicCheckerConfig()
DEFAULT_LEGAL_CHECKER = LegalCheckerConfig()


def get_default_checker_settings(ruleset_id: str) -> RulesetCheckerSettingsResponse:
    """
    Gibt Standard-Checker-Einstellungen zurück.

    Args:
        ruleset_id: Ruleset-ID

    Returns:
        Standard-Checker-Einstellungen
    """
    return RulesetCheckerSettingsResponse(
        ruleset_id=ruleset_id,
        risk_checker=DEFAULT_RISK_CHECKER,
        semantic_checker=DEFAULT_SEMANTIC_CHECKER,
        economic_checker=DEFAULT_ECONOMIC_CHECKER,
        legal_checker=DEFAULT_LEGAL_CHECKER,
    )
