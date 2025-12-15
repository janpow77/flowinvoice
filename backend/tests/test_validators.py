# Pfad: /backend/tests/test_validators.py
"""
FlowAudit Validator Tests

Tests für Validierungsfunktionen.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.services.validators import (
    ValidationStatus,
    is_small_amount_invoice,
    parse_amount,
    parse_date,
    validate_amount,
    validate_amount_calculation,
    validate_date,
    validate_eu_vat_id,
    validate_german_tax_id,
    validate_german_vat_id,
    validate_iban,
    validate_invoice_number,
    validate_uk_vat_id,
    validate_vat_rate,
)


class TestGermanTaxId:
    """Tests für deutsche Steuernummer."""

    def test_valid_format_berlin(self):
        result = validate_german_tax_id("12/345/67890")
        assert result.status == ValidationStatus.VALID

    def test_valid_format_bayern(self):
        result = validate_german_tax_id("123/456/78901")
        assert result.status == ValidationStatus.VALID

    def test_valid_format_nrw(self):
        result = validate_german_tax_id("123/4567/8901")
        assert result.status == ValidationStatus.VALID

    def test_valid_without_separator(self):
        result = validate_german_tax_id("12345678901")
        assert result.status == ValidationStatus.VALID

    def test_invalid_format(self):
        result = validate_german_tax_id("ABC123")
        assert result.status == ValidationStatus.INVALID

    def test_missing_value(self):
        result = validate_german_tax_id(None)
        assert result.status == ValidationStatus.MISSING

    def test_empty_value(self):
        result = validate_german_tax_id("")
        assert result.status == ValidationStatus.MISSING


class TestGermanVatId:
    """Tests für deutsche USt-ID."""

    def test_valid_format(self):
        result = validate_german_vat_id("DE123456789")
        assert result.status == ValidationStatus.VALID

    def test_valid_with_space(self):
        result = validate_german_vat_id("DE 123456789")
        assert result.status == ValidationStatus.VALID

    def test_valid_lowercase(self):
        result = validate_german_vat_id("de123456789")
        assert result.status == ValidationStatus.VALID

    def test_invalid_wrong_country(self):
        result = validate_german_vat_id("AT123456789")
        assert result.status == ValidationStatus.INVALID

    def test_invalid_wrong_length(self):
        result = validate_german_vat_id("DE12345678")  # 8 statt 9
        assert result.status == ValidationStatus.INVALID

    def test_missing_value(self):
        result = validate_german_vat_id(None)
        assert result.status == ValidationStatus.MISSING


class TestEuVatId:
    """Tests für EU USt-ID."""

    @pytest.mark.parametrize("vat_id,expected", [
        ("ATU12345678", ValidationStatus.VALID),
        ("BE0123456789", ValidationStatus.VALID),
        ("DE123456789", ValidationStatus.VALID),
        ("FR12123456789", ValidationStatus.VALID),
        ("NL123456789B01", ValidationStatus.VALID),
        ("IT12345678901", ValidationStatus.VALID),
        ("PL1234567890", ValidationStatus.VALID),
    ])
    def test_valid_eu_vat_ids(self, vat_id, expected):
        result = validate_eu_vat_id(vat_id)
        assert result.status == expected

    def test_invalid_format(self):
        result = validate_eu_vat_id("XX123456")
        assert result.status == ValidationStatus.INVALID

    def test_with_country_filter(self):
        result = validate_eu_vat_id("DE123456789", "DE")
        assert result.status == ValidationStatus.VALID

        result = validate_eu_vat_id("DE123456789", "AT")
        assert result.status == ValidationStatus.INVALID


class TestUkVatId:
    """Tests für UK VAT-Nummer."""

    def test_valid_9_digits(self):
        result = validate_uk_vat_id("GB123456789")
        assert result.status == ValidationStatus.VALID

    def test_valid_12_digits(self):
        result = validate_uk_vat_id("GB123456789012")
        assert result.status == ValidationStatus.VALID

    def test_invalid_format(self):
        result = validate_uk_vat_id("GB1234567")  # Zu kurz
        assert result.status == ValidationStatus.INVALID


class TestIban:
    """Tests für IBAN-Validierung."""

    def test_valid_german_iban(self):
        result = validate_iban("DE89370400440532013000")
        assert result.status == ValidationStatus.VALID

    def test_valid_with_spaces(self):
        result = validate_iban("DE89 3704 0044 0532 0130 00")
        assert result.status == ValidationStatus.VALID

    def test_valid_austrian_iban(self):
        result = validate_iban("AT611904300234573201")
        assert result.status == ValidationStatus.VALID

    def test_invalid_wrong_length(self):
        result = validate_iban("DE8937040044053201300")  # 21 statt 22
        assert result.status == ValidationStatus.INVALID

    def test_invalid_format(self):
        result = validate_iban("123456")
        assert result.status == ValidationStatus.INVALID


class TestInvoiceNumber:
    """Tests für Rechnungsnummer."""

    @pytest.mark.parametrize("inv_num", [
        "2025-001",
        "R-2025-0042",
        "INV/2025/00001",
        "20250315-001",
        "ABC123",
    ])
    def test_valid_invoice_numbers(self, inv_num):
        result = validate_invoice_number(inv_num)
        assert result.status == ValidationStatus.VALID

    def test_invalid_too_short(self):
        result = validate_invoice_number("AB")
        assert result.status == ValidationStatus.INVALID

    def test_invalid_special_chars(self):
        result = validate_invoice_number("INV@2025#001")
        assert result.status == ValidationStatus.INVALID


class TestDateValidation:
    """Tests für Datumsvalidierung."""

    def test_parse_german_date(self):
        result = parse_date("15.12.2025")
        assert result == date(2025, 12, 15)

    def test_parse_iso_date(self):
        result = parse_date("2025-12-15")
        assert result == date(2025, 12, 15)

    def test_parse_written_german(self):
        result = parse_date("15. Dezember 2025")
        assert result == date(2025, 12, 15)

    def test_validate_valid_date(self):
        result = validate_date("15.12.2025", "invoice_date")
        assert result.status == ValidationStatus.VALID

    def test_validate_future_date(self):
        # Datum in ferner Zukunft
        result = validate_date("15.12.2099", "invoice_date", max_date=date(2025, 12, 31))
        assert result.status == ValidationStatus.INVALID

    def test_validate_invalid_format(self):
        result = validate_date("not-a-date", "invoice_date")
        assert result.status == ValidationStatus.INVALID


class TestAmountValidation:
    """Tests für Betragsvalidierung."""

    def test_parse_german_amount(self):
        result = parse_amount("1.234,56")
        assert result == Decimal("1234.56")

    def test_parse_english_amount(self):
        result = parse_amount("1,234.56", "en")
        assert result == Decimal("1234.56")

    def test_parse_simple_amount(self):
        result = parse_amount("1234,56")
        assert result == Decimal("1234.56")

    def test_parse_with_euro_symbol(self):
        result = parse_amount("1.234,56 €")
        assert result == Decimal("1234.56")

    def test_validate_positive_amount(self):
        result = validate_amount(Decimal("100.00"), "net_amount", min_value=Decimal("0.01"))
        assert result.status == ValidationStatus.VALID

    def test_validate_zero_amount(self):
        result = validate_amount(Decimal("0.00"), "net_amount", min_value=Decimal("0.01"))
        assert result.status == ValidationStatus.INVALID


class TestVatRate:
    """Tests für MwSt-Satz."""

    def test_valid_german_standard(self):
        result = validate_vat_rate(19, "DE")
        assert result.status == ValidationStatus.VALID

    def test_valid_german_reduced(self):
        result = validate_vat_rate(7, "DE")
        assert result.status == ValidationStatus.VALID

    def test_unusual_rate(self):
        result = validate_vat_rate(15, "DE")
        assert result.status == ValidationStatus.WARNING

    def test_valid_uk_rate(self):
        result = validate_vat_rate(20, "UK")
        assert result.status == ValidationStatus.VALID


class TestAmountCalculation:
    """Tests für rechnerische Prüfung."""

    def test_correct_calculation(self):
        result = validate_amount_calculation(
            net_amount=Decimal("1000.00"),
            vat_amount=Decimal("190.00"),
            gross_amount=Decimal("1190.00"),
            vat_rate=19,
        )
        assert result.status == ValidationStatus.VALID

    def test_calculation_error(self):
        result = validate_amount_calculation(
            net_amount=Decimal("1000.00"),
            vat_amount=Decimal("190.00"),
            gross_amount=Decimal("1200.00"),  # Falsch!
        )
        assert result.status == ValidationStatus.INVALID

    def test_tolerance(self):
        # Kleine Rundungsdifferenz
        result = validate_amount_calculation(
            net_amount=Decimal("1000.00"),
            vat_amount=Decimal("190.00"),
            gross_amount=Decimal("1190.04"),
            tolerance=Decimal("0.05"),
        )
        assert result.status == ValidationStatus.VALID

    def test_missing_values(self):
        result = validate_amount_calculation(
            net_amount=None,
            vat_amount=None,
            gross_amount=Decimal("1190.00"),
        )
        assert result.status == ValidationStatus.MISSING


class TestSmallAmountInvoice:
    """Tests für Kleinbetragsrechnung."""

    def test_under_threshold_de(self):
        assert is_small_amount_invoice(Decimal("200.00"), "DE") is True

    def test_at_threshold_de(self):
        assert is_small_amount_invoice(Decimal("250.00"), "DE") is True

    def test_over_threshold_de(self):
        assert is_small_amount_invoice(Decimal("300.00"), "DE") is False

    def test_under_threshold_eu(self):
        assert is_small_amount_invoice(Decimal("350.00"), "EU") is True

    def test_over_threshold_eu(self):
        assert is_small_amount_invoice(Decimal("450.00"), "EU") is False
