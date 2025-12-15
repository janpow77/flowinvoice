# Pfad: /backend/app/schemas/project.py
"""
FlowAudit Project Schemas

Schemas für Vorhaben/Projekte.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import DateRange, Money


class BeneficiarySchema(BaseModel):
    """Begünstigter (Zuwendungsempfänger)."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Name des Begünstigten")
    legal_form: str | None = Field(default=None, description="Rechtsform")
    street: str = Field(..., description="Straße und Hausnummer")
    zip: str = Field(..., description="Postleitzahl")
    city: str = Field(..., description="Stadt")
    country: str = Field(default="DE", description="Ländercode (ISO 3166-1 alpha-2)")
    vat_id: str | None = Field(default=None, description="USt-IdNr.")
    tax_number: str | None = Field(default=None, description="Steuernummer")
    input_tax_deductible: bool = Field(
        default=True, description="Vorsteuerabzugsberechtigt"
    )
    aliases: list[str] = Field(
        default_factory=list, description="Alternative Schreibweisen"
    )


class ImplementationSchema(BaseModel):
    """Durchführungsort des Vorhabens."""

    model_config = ConfigDict(from_attributes=True)

    location_name: str = Field(..., description="Name des Durchführungsorts")
    street: str | None = Field(default=None, description="Straße")
    zip: str | None = Field(default=None, description="Postleitzahl")
    city: str | None = Field(default=None, description="Stadt")
    country: str = Field(default="DE", description="Land")
    description: str | None = Field(default=None, description="Beschreibung")


class ProjectSchema(BaseModel):
    """Projekt-Details."""

    model_config = ConfigDict(from_attributes=True)

    project_title: str = Field(..., description="Projekttitel")
    file_reference: str | None = Field(default=None, description="Aktenzeichen")
    project_description: str | None = Field(default=None, description="Beschreibung")
    implementation: ImplementationSchema | None = Field(
        default=None, description="Durchführungsort"
    )
    total_budget: Money | None = Field(default=None, description="Gesamtbudget")
    funding_type: str | None = Field(
        default=None, description="Förderart (PERCENT, FIXED)"
    )
    funding_rate_percent: float | None = Field(
        default=None, description="Fördersatz in %"
    )
    funding_fixed_amount: Money | None = Field(
        default=None, description="Fester Förderbetrag"
    )
    eligible_cost_categories: list[str] = Field(
        default_factory=list, description="Förderfähige Kostenarten"
    )
    project_period: DateRange | None = Field(
        default=None, description="Projektzeitraum"
    )
    approval_date: str | None = Field(default=None, description="Bewilligungsdatum")
    approving_authority: str | None = Field(
        default=None, description="Bewilligungsbehörde"
    )


class ProjectCreate(BaseModel):
    """Projekt erstellen."""

    model_config = ConfigDict(from_attributes=True)

    ruleset_id_hint: str | None = Field(default=None, description="Ruleset-Hinweis")
    ui_language_hint: str = Field(default="de", description="UI-Sprache")
    beneficiary: BeneficiarySchema = Field(..., description="Begünstigter")
    project: ProjectSchema = Field(..., description="Projekt-Details")


class ProjectUpdate(BaseModel):
    """Projekt aktualisieren."""

    model_config = ConfigDict(from_attributes=True)

    ruleset_id_hint: str | None = None
    ui_language_hint: str | None = None
    beneficiary: BeneficiarySchema | None = None
    project: ProjectSchema | None = None


class ProjectResponse(BaseModel):
    """Projekt-Response."""

    model_config = ConfigDict(from_attributes=True)

    project_id: str = Field(..., alias="id", description="Projekt-ID")
    ruleset_id_hint: str | None = Field(default=None, description="Ruleset-Hinweis")
    ui_language_hint: str = Field(default="de", description="UI-Sprache")
    beneficiary: BeneficiarySchema = Field(..., description="Begünstigter")
    project: ProjectSchema = Field(..., description="Projekt-Details")
    is_active: bool = Field(default=False, description="Aktives Projekt")
    created_at: datetime = Field(..., description="Erstellungszeitpunkt")
    updated_at: datetime | None = Field(default=None, description="Aktualisierung")


class ProjectListItem(BaseModel):
    """Projekt in Listenansicht."""

    model_config = ConfigDict(from_attributes=True)

    project_id: str = Field(..., description="Projekt-ID")
    project_title: str = Field(..., description="Projekttitel")
    file_reference: str | None = Field(default=None, description="Aktenzeichen")
    beneficiary_name: str = Field(..., description="Begünstigter")
    ruleset_id_hint: str | None = Field(default=None, description="Ruleset")
    is_active: bool = Field(default=False, description="Aktiv")
    document_count: int = Field(default=0, description="Anzahl Dokumente")
    created_at: datetime = Field(..., description="Erstellt")
