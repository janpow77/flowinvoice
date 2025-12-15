# Pfad: /backend/app/schemas/risk.py
"""
Risk Assessment Schema

Strukturen für die Risikobewertung von Rechnungen.
Didaktischer Hinweis: Mögliche Risiken - keine rechtliche Bewertung.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import RiskIndicator, Severity


class RiskFinding(BaseModel):
    """Einzelnes Risiko-Finding."""

    indicator: RiskIndicator = Field(
        ..., description="Art des Risikoindikators"
    )
    severity: Severity = Field(
        ..., description="Schweregrad des Risikos"
    )
    description: str = Field(
        ..., description="Beschreibung des erkannten Risikos"
    )
    evidence: str = Field(
        ..., description="Beleg/Nachweis für das Risiko"
    )
    recommendation: str = Field(
        ..., description="Empfehlung zur weiteren Prüfung"
    )

    # Didaktischer Hinweis
    disclaimer: str = Field(
        default="HINWEIS: Mögliches Risiko erkannt – keine rechtliche Bewertung",
        description="Didaktischer Disclaimer",
    )


class RiskContext(BaseModel):
    """Kontext für Risikobewertung."""

    # Statistische Vergleichsdaten
    median_amount: Optional[float] = Field(
        default=None, description="Median-Betrag vergleichbarer Rechnungen"
    )
    std_deviation: Optional[float] = Field(
        default=None, description="Standardabweichung der Beträge"
    )
    vendor_frequency: Optional[int] = Field(
        default=None, description="Anzahl Rechnungen dieses Lieferanten"
    )
    total_vendor_count: Optional[int] = Field(
        default=None, description="Gesamtanzahl verschiedener Lieferanten"
    )

    # Projektzeitraum
    project_start: Optional[date] = Field(
        default=None, description="Projektbeginn"
    )
    project_end: Optional[date] = Field(
        default=None, description="Projektende"
    )


class RiskAssessmentRequest(BaseModel):
    """Anfrage für Risikobewertung."""

    # Rechnungsdaten
    invoice_id: Optional[str] = Field(
        default=None, description="Rechnungs-ID"
    )
    vendor_name: str = Field(
        ..., description="Lieferantenname"
    )
    invoice_date: date = Field(
        ..., description="Rechnungsdatum"
    )
    net_amount: float = Field(
        ..., description="Nettobetrag"
    )
    gross_amount: float = Field(
        ..., description="Bruttobetrag"
    )
    description: str = Field(
        ..., description="Leistungsbeschreibung"
    )
    service_period_start: Optional[date] = Field(
        default=None, description="Beginn Leistungszeitraum"
    )
    service_period_end: Optional[date] = Field(
        default=None, description="Ende Leistungszeitraum"
    )
    invoice_recipient: Optional[str] = Field(
        default=None, description="Rechnungsempfänger"
    )

    # Vergleichskontext
    context: Optional[RiskContext] = Field(
        default=None, description="Statistischer Kontext"
    )

    # Begünstigtendaten
    beneficiary_name: Optional[str] = Field(
        default=None, description="Name des Begünstigten"
    )


class RiskAssessmentResult(BaseModel):
    """Ergebnis der Risikobewertung."""

    # Erkannte Risiken
    findings: list[RiskFinding] = Field(
        default_factory=list,
        description="Liste erkannter Risiko-Findings",
    )

    # Zusammenfassung
    risk_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Aggregierter Risiko-Score (0.0-1.0)",
    )
    highest_severity: Optional[Severity] = Field(
        default=None,
        description="Höchster erkannter Schweregrad",
    )
    summary: str = Field(
        default="Keine besonderen Risiken erkannt",
        description="Zusammenfassung der Risikobewertung",
    )

    # Metadaten
    assessment_timestamp: str = Field(
        ..., description="Zeitstempel der Bewertung (ISO 8601)"
    )
    assessment_version: str = Field(
        default="1.0.0", description="Version des Risikomoduls"
    )

    # Didaktischer Hinweis
    disclaimer: str = Field(
        default="Diese Risikobewertung dient didaktischen Zwecken und ersetzt keine rechtliche Prüfung.",
        description="Allgemeiner Disclaimer",
    )

    @property
    def has_risks(self) -> bool:
        """Prüft ob Risiken erkannt wurden."""
        return len(self.findings) > 0
