# Pfad: /backend/app/schemas/ruleset.py
"""
FlowAudit Ruleset Schemas

Schemas für Regelwerke (DE_USTG, EU_VAT, UK_VAT).
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LegalReference(BaseModel):
    """Rechtliche Referenz."""

    model_config = ConfigDict(from_attributes=True)

    law: str = Field(..., description="Gesetz/Richtlinie")
    section: str = Field(..., description="Paragraph/Artikel")
    description_de: str | None = Field(default=None, description="Beschreibung (DE)")
    description_en: str | None = Field(default=None, description="Beschreibung (EN)")


class ValidationRules(BaseModel):
    """Validierungsregeln für ein Feature."""

    model_config = ConfigDict(from_attributes=True)

    regex: str | None = Field(default=None, description="Regex-Pattern")
    min_length: int | None = Field(default=None, description="Mindestlänge")
    max_length: int | None = Field(default=None, description="Maximallänge")
    pattern: str | None = Field(default=None, description="Benanntes Pattern")
    must_contain_one_of: list[str] | None = Field(
        default=None, description="Muss eines enthalten"
    )


class GeneratorRules(BaseModel):
    """Generator-Regeln für ein Feature."""

    model_config = ConfigDict(from_attributes=True)

    can_be_missing: bool = Field(default=True, description="Kann fehlen")
    can_be_malformed: bool = Field(default=True, description="Kann fehlerhaft sein")
    typical_errors: list[str] | None = Field(default=None, description="Typische Fehler")
    omit_probability_default: float = Field(default=0.0, description="Standard-Auslassrate")


class FeatureSchema(BaseModel):
    """Feature-Definition eines Rulesets."""

    model_config = ConfigDict(from_attributes=True)

    feature_id: str = Field(..., description="Eindeutige Feature-ID")
    name_de: str | None = Field(default=None, description="Name (DE)")
    name_en: str | None = Field(default=None, description="Name (EN)")
    legal_basis: str = Field(..., description="Rechtsgrundlage")
    required_level: str = Field(..., description="REQUIRED | CONDITIONAL | OPTIONAL")
    extraction_type: str = Field(..., description="STRING | TEXTBLOCK | DATE | MONEY etc.")
    category: str | None = Field(
        default=None, description="IDENTITY | DATE | AMOUNT | TAX | TEXT | SEMANTIC"
    )
    validation: ValidationRules | None = Field(default=None, description="Validierungsregeln")
    semantic_meaning_de: str | None = Field(default=None, description="Semantik (DE)")
    semantic_meaning_en: str | None = Field(default=None, description="Semantik (EN)")
    explanation_de: str | None = Field(default=None, description="Erklärung (DE)")
    explanation_en: str | None = Field(default=None, description="Erklärung (EN)")
    generator_rules: GeneratorRules | None = Field(
        default=None, description="Generator-Regeln"
    )
    condition: str | None = Field(
        default=None, description="Bedingung (bei CONDITIONAL)"
    )
    applies_to: dict[str, bool] | None = Field(
        default=None, description="Anwendbarkeit"
    )


class SpecialRules(BaseModel):
    """Sonderregeln (z.B. Kleinbetragsrechnung)."""

    model_config = ConfigDict(from_attributes=True)

    small_amount_threshold_eur: float | None = Field(
        default=None, description="Schwelle Kleinbetragsrechnung (EUR)"
    )
    small_amount_threshold_gbp: float | None = Field(
        default=None, description="Schwelle Kleinbetragsrechnung (GBP)"
    )
    small_amount_reduced_fields: list[str] | None = Field(
        default=None, description="Reduzierte Felder"
    )
    simplified_invoice_threshold_gbp: float | None = Field(
        default=None, description="Schwelle vereinfachte Rechnung (GBP)"
    )
    simplified_invoice_fields: list[str] | None = Field(
        default=None, description="Felder vereinfachte Rechnung"
    )


class RulesetListItem(BaseModel):
    """Ruleset in Listenansicht."""

    model_config = ConfigDict(from_attributes=True)

    ruleset_id: str = Field(..., description="Ruleset-ID")
    version: str = Field(..., description="Version")
    title: str = Field(..., description="Titel (lokalisiert)")
    language_support: list[str] = Field(..., description="Unterstützte Sprachen")
    supported_document_types: list[str] = Field(
        default=["INVOICE"], description="Unterstützte Dokumenttypen"
    )


class RulesetResponse(BaseModel):
    """Vollständiges Ruleset."""

    model_config = ConfigDict(from_attributes=True)

    ruleset_id: str = Field(..., description="Ruleset-ID (DE_USTG, EU_VAT, UK_VAT)")
    version: str = Field(..., description="Version (semver)")
    jurisdiction: str = Field(..., description="Jurisdiktion (DE, EU, UK)")
    title_de: str = Field(..., description="Titel (DE)")
    title_en: str = Field(..., description="Titel (EN)")
    legal_references: list[LegalReference] = Field(..., description="Rechtsgrundlagen")
    default_language: str = Field(default="de", description="Standardsprache")
    supported_ui_languages: list[str] = Field(
        default=["de", "en"], description="UI-Sprachen"
    )
    currency_default: str = Field(default="EUR", description="Standardwährung")
    supported_document_types: list[str] = Field(
        default=["INVOICE"], description="Unterstützte Dokumenttypen"
    )
    features: list[FeatureSchema] = Field(..., description="Feature-Definitionen")
    special_rules: SpecialRules | None = Field(default=None, description="Sonderregeln")
    created_at: datetime = Field(..., description="Erstellungszeitpunkt")
    updated_at: datetime | None = Field(default=None, description="Aktualisierung")


class RulesetCreate(BaseModel):
    """Ruleset erstellen/aktualisieren."""

    model_config = ConfigDict(from_attributes=True)

    ruleset_id: str = Field(..., description="Ruleset-ID")
    version: str = Field(..., description="Version")
    jurisdiction: str = Field(..., description="Jurisdiktion")
    title_de: str = Field(..., description="Titel (DE)")
    title_en: str = Field(..., description="Titel (EN)")
    legal_references: list[dict[str, Any]] = Field(..., description="Rechtsgrundlagen")
    features: list[dict[str, Any]] = Field(..., description="Features")
    default_language: str = Field(default="de")
    supported_ui_languages: list[str] = Field(default=["de", "en"])
    currency_default: str = Field(default="EUR")
    special_rules: dict[str, Any] | None = Field(default=None)
