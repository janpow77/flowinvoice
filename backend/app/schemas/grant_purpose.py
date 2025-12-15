# Pfad: /backend/app/schemas/grant_purpose.py
"""
Grant Purpose Audit Schema (Zuwendungszweckprüfung)

Strukturierte Prüfung des sachlichen, zeitlichen, organisatorischen
und wirtschaftlichen Zusammenhangs einer Rechnung mit dem Förderzweck.
"""

from datetime import date

from pydantic import BaseModel, Field

from app.models.enums import (
    DimensionResult,
    GrantPurposeDimension,
    UnclearReason,
)


class DimensionAssessment(BaseModel):
    """Bewertung einer einzelnen Prüfdimension."""

    dimension: GrantPurposeDimension = Field(
        ..., description="Prüfdimension"
    )
    result: DimensionResult = Field(
        ..., description="Bewertungsergebnis"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Konfidenz der Bewertung (0.0-1.0)",
    )
    reasoning: str = Field(
        ..., description="Begründung für die Bewertung"
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Belege/Nachweise für die Bewertung",
    )

    # Pflichtangaben bei UNCLEAR
    unclear_reason: UnclearReason | None = Field(
        default=None,
        description="Grund für UNCLEAR-Status (Pflicht bei result=UNCLEAR)",
    )
    required_clarification: str | None = Field(
        default=None,
        description="Benötigte Information zur Klärung",
    )


class NegativeIndicator(BaseModel):
    """Negativindikator für Zuwendungszweckprüfung."""

    indicator_type: str = Field(
        ..., description="Art des Negativindikators"
    )
    description: str = Field(
        ..., description="Beschreibung des Problems"
    )
    severity: str = Field(
        default="MEDIUM",
        description="Schweregrad: LOW, MEDIUM, HIGH",
    )
    affected_dimension: GrantPurposeDimension = Field(
        ..., description="Betroffene Prüfdimension"
    )


class GrantPurposeAuditRequest(BaseModel):
    """Anfrage für Zuwendungszweckprüfung."""

    # Rechnungsdaten
    invoice_description: str = Field(
        ..., description="Leistungsbeschreibung der Rechnung"
    )
    invoice_date: date = Field(
        ..., description="Rechnungsdatum"
    )
    service_period_start: date | None = Field(
        default=None, description="Beginn Leistungszeitraum"
    )
    service_period_end: date | None = Field(
        default=None, description="Ende Leistungszeitraum"
    )
    net_amount: float = Field(
        ..., description="Nettobetrag in EUR"
    )
    vendor_name: str = Field(
        ..., description="Lieferantenname"
    )
    invoice_recipient: str = Field(
        ..., description="Rechnungsempfänger"
    )

    # Projektkontext
    project_name: str | None = Field(
        default=None, description="Projektname"
    )
    project_description: str | None = Field(
        default=None, description="Projektbeschreibung"
    )
    project_start: date | None = Field(
        default=None, description="Projektbeginn"
    )
    project_end: date | None = Field(
        default=None, description="Projektende"
    )

    # Begünstigtendaten
    beneficiary_name: str | None = Field(
        default=None, description="Name des Begünstigten"
    )
    beneficiary_aliases: list[str] = Field(
        default_factory=list,
        description="Alternative Schreibweisen des Begünstigten",
    )


class GrantPurposeAuditResult(BaseModel):
    """Ergebnis der Zuwendungszweckprüfung."""

    # Einzelbewertungen pro Dimension
    subject_relation: DimensionAssessment = Field(
        ..., description="Sachlicher Zusammenhang"
    )
    temporal_relation: DimensionAssessment = Field(
        ..., description="Zeitlicher Zusammenhang"
    )
    organizational_relation: DimensionAssessment = Field(
        ..., description="Organisatorischer Zusammenhang"
    )
    economic_plausibility: DimensionAssessment = Field(
        ..., description="Wirtschaftliche Plausibilität"
    )

    # Gesamtbewertung (algorithmisch abgeleitet)
    overall_result: DimensionResult = Field(
        ..., description="Gesamtergebnis der Prüfung"
    )
    overall_reasoning: str = Field(
        ..., description="Zusammenfassende Begründung"
    )

    # Erkannte Negativindikatoren
    negative_indicators: list[NegativeIndicator] = Field(
        default_factory=list,
        description="Erkannte Negativindikatoren",
    )

    # Prüfungsmetadaten
    audit_timestamp: str = Field(
        ..., description="Zeitstempel der Prüfung (ISO 8601)"
    )
    audit_version: str = Field(
        default="1.0.0", description="Version des Prüfalgorithmus"
    )

    def derive_overall_result(self) -> DimensionResult:
        """
        Leitet Gesamtergebnis algorithmisch ab.

        Regel:
        - min. 1x FAIL → FAIL
        - 0x FAIL, min. 1x UNCLEAR → UNCLEAR
        - nur PASS → PASS
        """
        results = [
            self.subject_relation.result,
            self.temporal_relation.result,
            self.organizational_relation.result,
            self.economic_plausibility.result,
        ]

        if DimensionResult.FAIL in results:
            return DimensionResult.FAIL
        if DimensionResult.UNCLEAR in results:
            return DimensionResult.UNCLEAR
        return DimensionResult.PASS


# Vordefinierte Negativindikatoren
NEGATIVE_INDICATORS = {
    "NO_PROJECT_REFERENCE": NegativeIndicator(
        indicator_type="NO_PROJECT_REFERENCE",
        description="Leistungsbeschreibung ohne erkennbaren Projektbezug",
        severity="MEDIUM",
        affected_dimension=GrantPurposeDimension.SUBJECT_RELATION,
    ),
    "OUTSIDE_PROJECT_PERIOD": NegativeIndicator(
        indicator_type="OUTSIDE_PROJECT_PERIOD",
        description="Leistungszeitraum außerhalb der Förderperiode",
        severity="HIGH",
        affected_dimension=GrantPurposeDimension.TEMPORAL_RELATION,
    ),
    "RECIPIENT_MISMATCH": NegativeIndicator(
        indicator_type="RECIPIENT_MISMATCH",
        description="Rechnungsempfänger entspricht nicht dem Begünstigten",
        severity="HIGH",
        affected_dimension=GrantPurposeDimension.ORGANIZATIONAL_RELATION,
    ),
    "GENERIC_SERVICE": NegativeIndicator(
        indicator_type="GENERIC_SERVICE",
        description="Pauschale Allgemeinleistungen ohne spezifischen Bezug",
        severity="MEDIUM",
        affected_dimension=GrantPurposeDimension.SUBJECT_RELATION,
    ),
    "UNUSUALLY_HIGH_AMOUNT": NegativeIndicator(
        indicator_type="UNUSUALLY_HIGH_AMOUNT",
        description="Ungewöhnlich hoher Betrag für die Leistungsart",
        severity="MEDIUM",
        affected_dimension=GrantPurposeDimension.ECONOMIC_PLAUSIBILITY,
    ),
    "MISSING_SERVICE_PERIOD": NegativeIndicator(
        indicator_type="MISSING_SERVICE_PERIOD",
        description="Fehlende Angabe des Leistungszeitraums",
        severity="LOW",
        affected_dimension=GrantPurposeDimension.TEMPORAL_RELATION,
    ),
}
