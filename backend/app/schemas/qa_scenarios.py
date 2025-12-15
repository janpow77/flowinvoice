# Pfad: /backend/app/schemas/qa_scenarios.py
"""
QA Reference Scenarios for Generator

Definiert Referenzszenarien für die Qualitätssicherung.
Bei identischem Szenario müssen Ergebnisse vergleichbar sein.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ReferenceScenarioType(str, Enum):
    """Typen von Referenzszenarien."""

    # Korrekte Rechnungen
    REF_CORRECT = "REF_CORRECT"  # Formal korrekte Rechnung

    # Fehlerhafte Rechnungen
    REF_MISSING_FIELD = "REF_MISSING_FIELD"  # Fehlende Pflichtangabe
    REF_UNCLEAR_PURPOSE = "REF_UNCLEAR_PURPOSE"  # Unklarer Zuwendungszweck
    REF_WRONG_RECIPIENT = "REF_WRONG_RECIPIENT"  # Falscher Empfänger
    REF_OUTSIDE_PERIOD = "REF_OUTSIDE_PERIOD"  # Außerhalb Projektzeitraum
    REF_HIGH_AMOUNT = "REF_HIGH_AMOUNT"  # Ungewöhnlich hoher Betrag

    # Grenzfälle
    REF_EDGE_SMALL_AMOUNT = "REF_EDGE_SMALL_AMOUNT"  # Kleinbetragsrechnung
    REF_EDGE_ALIAS_NAME = "REF_EDGE_ALIAS_NAME"  # Alias statt Hauptname
    REF_EDGE_PARTIAL_PERIOD = "REF_EDGE_PARTIAL_PERIOD"  # Teilweise im Zeitraum


class ExpectedResult(BaseModel):
    """Erwartetes Prüfergebnis für ein Szenario."""

    traffic_light: str = Field(
        ..., description="Erwartete Ampel: GREEN | YELLOW | RED"
    )
    expected_errors: list[str] = Field(
        default_factory=list,
        description="Erwartete Fehler-IDs",
    )
    expected_warnings: list[str] = Field(
        default_factory=list,
        description="Erwartete Warnungs-IDs",
    )
    grant_purpose_result: str | None = Field(
        default=None,
        description="Erwartetes Grant Purpose Ergebnis: PASS | FAIL | UNCLEAR",
    )
    risk_indicators: list[str] = Field(
        default_factory=list,
        description="Erwartete Risikoindikatoren",
    )


class ReferenceScenario(BaseModel):
    """Referenzszenario für QA-Tests."""

    scenario_id: ReferenceScenarioType = Field(
        ..., description="Szenario-Typ"
    )
    name: str = Field(
        ..., description="Sprechender Name"
    )
    description: str = Field(
        ..., description="Beschreibung des Szenarios"
    )

    # Generierte Rechnungsdaten
    invoice_data: dict[str, Any] = Field(
        ..., description="Rechnungsdaten für dieses Szenario"
    )

    # Erwartetes Ergebnis
    expected: ExpectedResult = Field(
        ..., description="Erwartetes Prüfergebnis"
    )

    # Didaktischer Hinweis
    learning_objective: str = Field(
        default="",
        description="Lernziel dieses Szenarios",
    )

    # Vergleichbarkeit
    deterministic: bool = Field(
        default=True,
        description="Ergebnis muss deterministisch sein",
    )
    tolerance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Toleranz bei Score-Vergleichen (0.0-1.0)",
    )


# ============================================================
# Vordefinierte Referenzszenarien
# ============================================================

REFERENCE_SCENARIOS: dict[ReferenceScenarioType, ReferenceScenario] = {
    ReferenceScenarioType.REF_CORRECT: ReferenceScenario(
        scenario_id=ReferenceScenarioType.REF_CORRECT,
        name="Korrekte Standardrechnung",
        description="Formal vollständig korrekte Rechnung mit allen Pflichtangaben",
        invoice_data={
            "vendor_name": "Muster GmbH",
            "vendor_address": "Musterstraße 1, 12345 Musterstadt",
            "vendor_vat_id": "DE123456789",
            "invoice_number": "2025-0001",
            "invoice_date": "2025-01-15",
            "service_period": "2025-01-01 bis 2025-01-31",
            "description": "IT-Beratung für Projekt Digitalisierung",
            "net_amount": 5000.00,
            "vat_rate": 19,
            "vat_amount": 950.00,
            "gross_amount": 5950.00,
            "customer_name": "Förderverein Musterstadt e.V.",
            "customer_address": "Hauptstraße 1, 12345 Musterstadt",
        },
        expected=ExpectedResult(
            traffic_light="GREEN",
            expected_errors=[],
            expected_warnings=[],
            grant_purpose_result="PASS",
            risk_indicators=[],
        ),
        learning_objective="Erkennen einer formal korrekten Rechnung",
        deterministic=True,
    ),

    ReferenceScenarioType.REF_MISSING_FIELD: ReferenceScenario(
        scenario_id=ReferenceScenarioType.REF_MISSING_FIELD,
        name="Fehlende Rechnungsnummer",
        description="Rechnung ohne Rechnungsnummer (Pflichtfeld nach UStG)",
        invoice_data={
            "vendor_name": "Muster GmbH",
            "vendor_address": "Musterstraße 1, 12345 Musterstadt",
            "vendor_vat_id": "DE123456789",
            "invoice_number": None,  # FEHLT
            "invoice_date": "2025-01-15",
            "description": "Beratungsleistungen",
            "net_amount": 3000.00,
            "vat_rate": 19,
            "vat_amount": 570.00,
            "gross_amount": 3570.00,
            "customer_name": "Förderverein Musterstadt e.V.",
        },
        expected=ExpectedResult(
            traffic_light="RED",
            expected_errors=["INVOICE_NUMBER_MISSING"],
            expected_warnings=[],
            grant_purpose_result=None,
            risk_indicators=[],
        ),
        learning_objective="Erkennen fehlender Pflichtangaben gem. UStG §14",
        deterministic=True,
    ),

    ReferenceScenarioType.REF_UNCLEAR_PURPOSE: ReferenceScenario(
        scenario_id=ReferenceScenarioType.REF_UNCLEAR_PURPOSE,
        name="Unklarer Verwendungszweck",
        description="Generische Leistungsbeschreibung ohne Projektbezug",
        invoice_data={
            "vendor_name": "Allround Service GmbH",
            "vendor_vat_id": "DE987654321",
            "invoice_number": "2025-0042",
            "invoice_date": "2025-01-20",
            "description": "Diverse Leistungen nach Aufwand",  # GENERISCH
            "net_amount": 8500.00,
            "vat_rate": 19,
            "vat_amount": 1615.00,
            "gross_amount": 10115.00,
            "customer_name": "Förderverein Musterstadt e.V.",
        },
        expected=ExpectedResult(
            traffic_light="YELLOW",
            expected_errors=[],
            expected_warnings=["GENERIC_DESCRIPTION"],
            grant_purpose_result="UNCLEAR",
            risk_indicators=["NO_PROJECT_REFERENCE"],
        ),
        learning_objective="Erkennen generischer Leistungsbeschreibungen ohne Projektbezug",
        deterministic=True,
    ),

    ReferenceScenarioType.REF_WRONG_RECIPIENT: ReferenceScenario(
        scenario_id=ReferenceScenarioType.REF_WRONG_RECIPIENT,
        name="Falscher Rechnungsempfänger",
        description="Empfänger entspricht nicht dem Begünstigten",
        invoice_data={
            "vendor_name": "Muster GmbH",
            "vendor_vat_id": "DE123456789",
            "invoice_number": "2025-0003",
            "invoice_date": "2025-01-18",
            "description": "Schulungsmaßnahme für Projekt XY",
            "net_amount": 2500.00,
            "vat_rate": 19,
            "vat_amount": 475.00,
            "gross_amount": 2975.00,
            "customer_name": "Andere Organisation e.V.",  # FALSCH
        },
        expected=ExpectedResult(
            traffic_light="RED",
            expected_errors=["BENEFICIARY_MISMATCH"],
            expected_warnings=[],
            grant_purpose_result="FAIL",
            risk_indicators=["RECIPIENT_MISMATCH"],
        ),
        learning_objective="Erkennen nicht übereinstimmender Empfänger/Begünstigter",
        deterministic=True,
    ),

    ReferenceScenarioType.REF_OUTSIDE_PERIOD: ReferenceScenario(
        scenario_id=ReferenceScenarioType.REF_OUTSIDE_PERIOD,
        name="Außerhalb Projektzeitraum",
        description="Leistungsdatum liegt außerhalb der Förderperiode",
        invoice_data={
            "vendor_name": "Muster GmbH",
            "vendor_vat_id": "DE123456789",
            "invoice_number": "2024-0099",
            "invoice_date": "2024-11-15",  # VOR Projektstart
            "service_period": "2024-10-01 bis 2024-10-31",  # VOR Projekt
            "description": "Vorbereitende Arbeiten",
            "net_amount": 4000.00,
            "vat_rate": 19,
            "vat_amount": 760.00,
            "gross_amount": 4760.00,
            "customer_name": "Förderverein Musterstadt e.V.",
        },
        expected=ExpectedResult(
            traffic_light="RED",
            expected_errors=["OUTSIDE_PROJECT_PERIOD"],
            expected_warnings=[],
            grant_purpose_result="FAIL",
            risk_indicators=["OUTSIDE_PROJECT_PERIOD"],
        ),
        learning_objective="Erkennen von Leistungen außerhalb der Förderperiode",
        deterministic=True,
    ),

    ReferenceScenarioType.REF_HIGH_AMOUNT: ReferenceScenario(
        scenario_id=ReferenceScenarioType.REF_HIGH_AMOUNT,
        name="Ungewöhnlich hoher Betrag",
        description="Einzelrechnung mit auffällig hohem Betrag",
        invoice_data={
            "vendor_name": "Premium Consulting AG",
            "vendor_vat_id": "DE111222333",
            "invoice_number": "2025-PREM-001",
            "invoice_date": "2025-01-22",
            "description": "Strategische Beratung Digitalisierung",
            "net_amount": 75000.00,  # HOHER BETRAG
            "vat_rate": 19,
            "vat_amount": 14250.00,
            "gross_amount": 89250.00,
            "customer_name": "Förderverein Musterstadt e.V.",
        },
        expected=ExpectedResult(
            traffic_light="YELLOW",
            expected_errors=[],
            expected_warnings=["HIGH_AMOUNT_WARNING"],
            grant_purpose_result="UNCLEAR",
            risk_indicators=["HIGH_AMOUNT"],
        ),
        learning_objective="Erkennen ungewöhnlich hoher Einzelbeträge",
        deterministic=True,
        tolerance=0.1,  # Score-Toleranz für Betragsvergleiche
    ),

    ReferenceScenarioType.REF_EDGE_SMALL_AMOUNT: ReferenceScenario(
        scenario_id=ReferenceScenarioType.REF_EDGE_SMALL_AMOUNT,
        name="Kleinbetragsrechnung",
        description="Rechnung unter Kleinbetragsgrenze (reduzierte Anforderungen)",
        invoice_data={
            "vendor_name": "Bürobedarf Schmidt",
            "vendor_vat_id": "DE555666777",
            "invoice_number": "K-2025-0001",
            "invoice_date": "2025-01-10",
            "description": "Büromaterial",
            "net_amount": 180.00,  # UNTER 250 EUR
            "vat_rate": 19,
            "vat_amount": 34.20,
            "gross_amount": 214.20,
            # Kein Kundenname erforderlich bei Kleinbetrag
        },
        expected=ExpectedResult(
            traffic_light="GREEN",
            expected_errors=[],
            expected_warnings=[],
            grant_purpose_result=None,
            risk_indicators=[],
        ),
        learning_objective="Verstehen der reduzierten Anforderungen bei Kleinbetragsrechnungen",
        deterministic=True,
    ),

    ReferenceScenarioType.REF_EDGE_ALIAS_NAME: ReferenceScenario(
        scenario_id=ReferenceScenarioType.REF_EDGE_ALIAS_NAME,
        name="Alias-Name verwendet",
        description="Bekannter Alias statt Hauptname des Begünstigten",
        invoice_data={
            "vendor_name": "Muster GmbH",
            "vendor_vat_id": "DE123456789",
            "invoice_number": "2025-0005",
            "invoice_date": "2025-01-25",
            "description": "Workshop-Durchführung",
            "net_amount": 1500.00,
            "vat_rate": 19,
            "vat_amount": 285.00,
            "gross_amount": 1785.00,
            "customer_name": "FV Musterstadt",  # ALIAS statt Hauptname
        },
        expected=ExpectedResult(
            traffic_light="GREEN",  # Alias ist bekannt
            expected_errors=[],
            expected_warnings=["ALIAS_USED"],
            grant_purpose_result="PASS",
            risk_indicators=[],
        ),
        learning_objective="Umgang mit bekannten Alias-Schreibweisen des Begünstigten",
        deterministic=True,
    ),

    ReferenceScenarioType.REF_EDGE_PARTIAL_PERIOD: ReferenceScenario(
        scenario_id=ReferenceScenarioType.REF_EDGE_PARTIAL_PERIOD,
        name="Teilweise im Projektzeitraum",
        description="Leistung beginnt vor Projektstart, endet im Projekt",
        invoice_data={
            "vendor_name": "Muster GmbH",
            "vendor_vat_id": "DE123456789",
            "invoice_number": "2025-0006",
            "invoice_date": "2025-01-30",
            "service_period": "2024-12-15 bis 2025-01-15",  # TEILWEISE
            "description": "Jahresübergreifende Beratung",
            "net_amount": 6000.00,
            "vat_rate": 19,
            "vat_amount": 1140.00,
            "gross_amount": 7140.00,
            "customer_name": "Förderverein Musterstadt e.V.",
        },
        expected=ExpectedResult(
            traffic_light="YELLOW",
            expected_errors=[],
            expected_warnings=["PARTIAL_PERIOD_COVERAGE"],
            grant_purpose_result="UNCLEAR",
            risk_indicators=["OUTSIDE_PROJECT_PERIOD"],
        ),
        learning_objective="Umgang mit zeitraumübergreifenden Leistungen",
        deterministic=True,
    ),
}


class ScenarioTestResult(BaseModel):
    """Ergebnis eines Szenario-Tests."""

    scenario_id: ReferenceScenarioType = Field(
        ..., description="Getestetes Szenario"
    )
    passed: bool = Field(
        ..., description="Test bestanden"
    )
    expected: ExpectedResult = Field(
        ..., description="Erwartetes Ergebnis"
    )
    actual_traffic_light: str = Field(
        ..., description="Tatsächliche Ampel"
    )
    actual_errors: list[str] = Field(
        default_factory=list,
        description="Tatsächliche Fehler",
    )
    deviation_notes: list[str] = Field(
        default_factory=list,
        description="Abweichungsnotizen",
    )
    model_effect: str | None = Field(
        default=None,
        description="Erkannter Modell-/Prompt-Effekt bei Abweichung",
    )


def get_scenario(scenario_type: ReferenceScenarioType) -> ReferenceScenario:
    """Gibt Referenzszenario zurück."""
    return REFERENCE_SCENARIOS[scenario_type]


def get_all_scenarios() -> list[ReferenceScenario]:
    """Gibt alle Referenzszenarien zurück."""
    return list(REFERENCE_SCENARIOS.values())
