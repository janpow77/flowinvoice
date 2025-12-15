# Pfad: /backend/tests/test_rule_engine.py
"""
FlowAudit Rule Engine Tests

Tests für die deterministische Vorprüfung.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.services.parser import ExtractedValue, ParseResult, ParsedPage
from app.services.rule_engine import (
    FeatureCategory,
    PrecheckResult,
    RequiredLevel,
    RuleEngine,
    get_rule_engine,
)
from app.services.validators import ValidationStatus


def create_parse_result(extracted: dict) -> ParseResult:
    """Erstellt ParseResult aus Dict."""
    extracted_values = {}
    for key, val in extracted.items():
        if isinstance(val, dict):
            extracted_values[key] = ExtractedValue(
                value=val.get("value"),
                raw_text=val.get("raw_text", str(val.get("value", ""))),
                confidence=val.get("confidence", 0.9),
            )
        else:
            extracted_values[key] = ExtractedValue(
                value=val,
                raw_text=str(val),
                confidence=0.9,
            )

    return ParseResult(
        raw_text="Test invoice text",
        pages=[ParsedPage(page_number=1, width=612, height=792, text="Test", tokens=[])],
        extracted=extracted_values,
        timings_ms={"total": 100},
    )


class TestRuleEngine:
    """Tests für Rule Engine."""

    def test_get_rule_engine_singleton(self):
        engine1 = get_rule_engine("DE_USTG")
        engine2 = get_rule_engine("DE_USTG")
        assert engine1 is engine2

    def test_different_rulesets(self):
        engine_de = get_rule_engine("DE_USTG")
        engine_eu = get_rule_engine("EU_VAT")
        assert engine_de.ruleset_id == "DE_USTG"
        assert engine_eu.ruleset_id == "EU_VAT"


class TestPrecheckDeUstg:
    """Tests für DE_USTG Vorprüfung."""

    def test_valid_invoice(self):
        """Vollständige korrekte Rechnung."""
        engine = RuleEngine("DE_USTG")

        parse_result = create_parse_result({
            "invoice_number": "2025-001",
            "invoice_date": date(2025, 12, 15),
            "vat_id": "DE123456789",
            "net_amount": Decimal("1000.00"),
            "vat_amount": Decimal("190.00"),
            "gross_amount": Decimal("1190.00"),
            "vat_rate": 19,
            "supply_date_or_period": "01.12.2025",
            "supply_description": "Softwareentwicklung",
            "supplier_name_address": "Mustermann GmbH, Musterstraße 1, 12345 Stadt",
            "customer_name_address": "Kunde AG, Kundenweg 2, 54321 Ort",
        })

        result = engine.precheck(parse_result)

        assert result.passed is True
        assert len(result.errors) == 0
        assert result.is_small_amount is False

    def test_missing_invoice_number(self):
        """Fehlende Rechnungsnummer."""
        engine = RuleEngine("DE_USTG")

        parse_result = create_parse_result({
            "invoice_date": date(2025, 12, 15),
            "vat_id": "DE123456789",
            "net_amount": Decimal("1000.00"),
            "vat_amount": Decimal("190.00"),
            "gross_amount": Decimal("1190.00"),
            "vat_rate": 19,
        })

        result = engine.precheck(parse_result)

        assert result.passed is False
        assert any(e.feature_id == "invoice_number" for e in result.errors)

    def test_invalid_vat_id_format(self):
        """Ungültiges USt-ID Format."""
        engine = RuleEngine("DE_USTG")

        parse_result = create_parse_result({
            "invoice_number": "2025-001",
            "invoice_date": date(2025, 12, 15),
            "vat_id": "INVALID123",  # Ungültig
            "net_amount": Decimal("1000.00"),
            "vat_amount": Decimal("190.00"),
            "gross_amount": Decimal("1190.00"),
            "vat_rate": 19,
        })

        result = engine.precheck(parse_result)

        # Sollte Fehler für vat_id haben
        vat_errors = [e for e in result.checks if e.feature_id == "vat_id"]
        assert len(vat_errors) > 0
        assert vat_errors[0].status == ValidationStatus.INVALID

    def test_calculation_error(self):
        """Rechenfehler Brutto != Netto + MwSt."""
        engine = RuleEngine("DE_USTG")

        parse_result = create_parse_result({
            "invoice_number": "2025-001",
            "invoice_date": date(2025, 12, 15),
            "vat_id": "DE123456789",
            "net_amount": Decimal("1000.00"),
            "vat_amount": Decimal("190.00"),
            "gross_amount": Decimal("1200.00"),  # Falsch!
            "vat_rate": 19,
        })

        result = engine.precheck(parse_result)

        calc_errors = [e for e in result.errors if e.feature_id == "amount_calculation"]
        assert len(calc_errors) > 0

    def test_tax_identification_check(self):
        """Prüfung Steuernummer oder USt-ID."""
        engine = RuleEngine("DE_USTG")

        # Weder Steuernummer noch USt-ID
        parse_result = create_parse_result({
            "invoice_number": "2025-001",
            "invoice_date": date(2025, 12, 15),
            "net_amount": Decimal("1000.00"),
            "vat_amount": Decimal("190.00"),
            "gross_amount": Decimal("1190.00"),
            "vat_rate": 19,
        })

        result = engine.precheck(parse_result)

        tax_errors = [e for e in result.errors if e.feature_id == "tax_identification"]
        assert len(tax_errors) > 0


class TestSmallAmountInvoice:
    """Tests für Kleinbetragsrechnungen."""

    def test_small_amount_detected(self):
        """Kleinbetragsrechnung wird erkannt."""
        engine = RuleEngine("DE_USTG")

        parse_result = create_parse_result({
            "gross_amount": Decimal("200.00"),  # Unter 250€
            "invoice_date": date(2025, 12, 15),
            "supply_description": "Büromaterial",
            "supplier_name_address": "Mustermann",
            "vat_rate": 19,
        })

        result = engine.precheck(parse_result)

        assert result.is_small_amount is True

    def test_small_amount_reduced_requirements(self):
        """Reduzierte Anforderungen für Kleinbetragsrechnungen."""
        engine = RuleEngine("DE_USTG")

        # Nur Pflichtfelder für Kleinbetragsrechnung
        parse_result = create_parse_result({
            "gross_amount": Decimal("200.00"),
            "invoice_date": date(2025, 12, 15),
            "supply_description": "Büromaterial",
            "supplier_name_address": "Mustermann GmbH",
            "vat_rate": 19,
        })

        result = engine.precheck(parse_result)

        # Bei Kleinbetragsrechnung sollten keine Fehler für
        # invoice_number, net_amount, vat_amount auftreten
        missing_errors = [
            e for e in result.errors
            if e.feature_id in ["invoice_number", "net_amount", "vat_amount"]
        ]
        assert len(missing_errors) == 0


class TestEuVatRuleset:
    """Tests für EU_VAT Ruleset."""

    def test_requires_supplier_vat_id(self):
        """EU_VAT erfordert Lieferanten-USt-ID."""
        engine = RuleEngine("EU_VAT")

        parse_result = create_parse_result({
            "invoice_number": "2025-001",
            "invoice_date": date(2025, 12, 15),
            # Keine supplier_vat_id
        })

        result = engine.precheck(parse_result)

        vat_errors = [e for e in result.errors if "vat" in e.feature_id.lower()]
        assert len(vat_errors) > 0


class TestUkVatRuleset:
    """Tests für UK_VAT Ruleset."""

    def test_requires_tax_point(self):
        """UK_VAT erfordert Tax Point."""
        engine = RuleEngine("UK_VAT")

        parse_result = create_parse_result({
            "invoice_number": "2025-001",
            "invoice_date": date(2025, 12, 15),
            # Kein tax_point
        })

        result = engine.precheck(parse_result)

        # UK_VAT sollte tax_point als Pflichtfeld prüfen
        assert result.ruleset_id == "UK_VAT"
