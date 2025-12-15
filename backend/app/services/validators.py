# Pfad: /backend/app/services/validators.py
"""
FlowAudit Validators

Validierungsfunktionen für steuerliche Merkmale.
Basiert auf rulesets.md Spezifikation.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any


class ValidationStatus(str, Enum):
    """Validierungsstatus."""

    VALID = "VALID"
    INVALID = "INVALID"
    MISSING = "MISSING"
    WARNING = "WARNING"


@dataclass
class ValidationResult:
    """Ergebnis einer Validierung."""

    status: ValidationStatus
    field: str
    value: Any = None
    message: str = ""
    details: dict[str, Any] | None = None


# =============================================================================
# Deutsche Steuernummer (§ 14 Abs. 4 UStG)
# =============================================================================

GERMAN_TAX_ID_PATTERNS = [
    r"^\d{2}/\d{3}/\d{5}$",  # 12/345/67890 (Berlin, etc.)
    r"^\d{3}/\d{3}/\d{5}$",  # 123/456/78901 (Bayern)
    r"^\d{3}/\d{4}/\d{4}$",  # 123/4567/8901 (NRW)
    r"^\d{2}\s?\d{3}\s?\d{5}$",  # Mit Leerzeichen
    r"^\d{10,11}$",  # Ohne Trennzeichen
]


def validate_german_tax_id(value: str | None) -> ValidationResult:
    """
    Prüft ob Wert einer deutschen Steuernummer entspricht.

    Args:
        value: Zu prüfender Wert

    Returns:
        ValidationResult
    """
    if not value:
        return ValidationResult(
            status=ValidationStatus.MISSING,
            field="tax_number",
            message="Steuernummer fehlt",
        )

    normalized = value.strip()

    for pattern in GERMAN_TAX_ID_PATTERNS:
        if re.match(pattern, normalized):
            return ValidationResult(
                status=ValidationStatus.VALID,
                field="tax_number",
                value=normalized,
            )

    return ValidationResult(
        status=ValidationStatus.INVALID,
        field="tax_number",
        value=value,
        message=f"Ungültiges Format für deutsche Steuernummer: {value}",
    )


# =============================================================================
# Deutsche USt-ID (DE + 9 Ziffern)
# =============================================================================

GERMAN_VAT_ID_PATTERN = r"^DE\d{9}$"


def validate_german_vat_id(value: str | None) -> ValidationResult:
    """
    Prüft deutsche USt-ID (DE + 9 Ziffern).

    Args:
        value: Zu prüfender Wert

    Returns:
        ValidationResult
    """
    if not value:
        return ValidationResult(
            status=ValidationStatus.MISSING,
            field="vat_id",
            message="USt-ID fehlt",
        )

    normalized = value.strip().upper().replace(" ", "")

    if re.match(GERMAN_VAT_ID_PATTERN, normalized):
        return ValidationResult(
            status=ValidationStatus.VALID,
            field="vat_id",
            value=normalized,
        )

    return ValidationResult(
        status=ValidationStatus.INVALID,
        field="vat_id",
        value=value,
        message=f"Ungültige deutsche USt-ID: {value} (erwartet: DE + 9 Ziffern)",
    )


# =============================================================================
# EU USt-ID Patterns (alle EU-Länder)
# =============================================================================

EU_VAT_ID_PATTERNS = {
    "AT": r"^ATU\d{8}$",  # Österreich
    "BE": r"^BE0?\d{9,10}$",  # Belgien
    "BG": r"^BG\d{9,10}$",  # Bulgarien
    "CY": r"^CY\d{8}[A-Z]$",  # Zypern
    "CZ": r"^CZ\d{8,10}$",  # Tschechien
    "DE": r"^DE\d{9}$",  # Deutschland
    "DK": r"^DK\d{8}$",  # Dänemark
    "EE": r"^EE\d{9}$",  # Estland
    "EL": r"^EL\d{9}$",  # Griechenland
    "ES": r"^ES[A-Z0-9]\d{7}[A-Z0-9]$",  # Spanien
    "FI": r"^FI\d{8}$",  # Finnland
    "FR": r"^FR[A-Z0-9]{2}\d{9}$",  # Frankreich
    "HR": r"^HR\d{11}$",  # Kroatien
    "HU": r"^HU\d{8}$",  # Ungarn
    "IE": r"^IE\d{7}[A-Z]{1,2}$",  # Irland
    "IT": r"^IT\d{11}$",  # Italien
    "LT": r"^LT(\d{9}|\d{12})$",  # Litauen
    "LU": r"^LU\d{8}$",  # Luxemburg
    "LV": r"^LV\d{11}$",  # Lettland
    "MT": r"^MT\d{8}$",  # Malta
    "NL": r"^NL\d{9}B\d{2}$",  # Niederlande
    "PL": r"^PL\d{10}$",  # Polen
    "PT": r"^PT\d{9}$",  # Portugal
    "RO": r"^RO\d{2,10}$",  # Rumänien
    "SE": r"^SE\d{12}$",  # Schweden
    "SI": r"^SI\d{8}$",  # Slowenien
    "SK": r"^SK\d{10}$",  # Slowakei
}


def validate_eu_vat_id(value: str | None, country_code: str | None = None) -> ValidationResult:
    """
    Prüft EU-USt-ID, optional mit Ländercode-Einschränkung.

    Args:
        value: Zu prüfender Wert
        country_code: Optionaler Ländercode (z.B. "DE", "AT")

    Returns:
        ValidationResult
    """
    if not value:
        return ValidationResult(
            status=ValidationStatus.MISSING,
            field="vat_id",
            message="EU-USt-ID fehlt",
        )

    normalized = value.strip().upper().replace(" ", "").replace("-", "")

    if country_code:
        pattern = EU_VAT_ID_PATTERNS.get(country_code)
        if pattern and re.match(pattern, normalized):
            return ValidationResult(
                status=ValidationStatus.VALID,
                field="vat_id",
                value=normalized,
                details={"country": country_code},
            )
        return ValidationResult(
            status=ValidationStatus.INVALID,
            field="vat_id",
            value=value,
            message=f"Ungültige USt-ID für {country_code}: {value}",
        )

    # Länderpräfix aus Wert extrahieren
    if len(normalized) >= 2:
        prefix = normalized[:2]
        pattern = EU_VAT_ID_PATTERNS.get(prefix)
        if pattern and re.match(pattern, normalized):
            return ValidationResult(
                status=ValidationStatus.VALID,
                field="vat_id",
                value=normalized,
                details={"country": prefix},
            )

    return ValidationResult(
        status=ValidationStatus.INVALID,
        field="vat_id",
        value=value,
        message=f"Ungültige EU-USt-ID: {value}",
    )


# =============================================================================
# UK VAT-Nummer
# =============================================================================

UK_VAT_PATTERNS = [
    r"^GB\d{9}$",  # Standard 9-stellig
    r"^GB\d{12}$",  # 12-stellig (mit Suffix)
]


def validate_uk_vat_id(value: str | None) -> ValidationResult:
    """
    Prüft UK VAT-Nummer.

    Args:
        value: Zu prüfender Wert

    Returns:
        ValidationResult
    """
    if not value:
        return ValidationResult(
            status=ValidationStatus.MISSING,
            field="vat_id",
            message="UK VAT-Nummer fehlt",
        )

    normalized = value.strip().upper().replace(" ", "").replace("-", "")

    for pattern in UK_VAT_PATTERNS:
        if re.match(pattern, normalized):
            return ValidationResult(
                status=ValidationStatus.VALID,
                field="vat_id",
                value=normalized,
            )

    return ValidationResult(
        status=ValidationStatus.INVALID,
        field="vat_id",
        value=value,
        message=f"Ungültige UK VAT-Nummer: {value}",
    )


# =============================================================================
# IBAN-Validierung
# =============================================================================

IBAN_LENGTHS = {
    "DE": 22,
    "AT": 20,
    "CH": 21,
    "FR": 27,
    "IT": 27,
    "ES": 24,
    "NL": 18,
    "BE": 16,
    "PL": 28,
    "GB": 22,
}


def validate_iban(value: str | None) -> ValidationResult:
    """
    Prüft IBAN-Format (ohne Prüfziffervalidierung).

    Args:
        value: Zu prüfender Wert

    Returns:
        ValidationResult
    """
    if not value:
        return ValidationResult(
            status=ValidationStatus.MISSING,
            field="iban",
            message="IBAN fehlt",
        )

    normalized = value.strip().upper().replace(" ", "")

    # Ländercode + 2 Prüfziffern + BBAN
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$", normalized):
        return ValidationResult(
            status=ValidationStatus.INVALID,
            field="iban",
            value=value,
            message=f"Ungültiges IBAN-Format: {value}",
        )

    # Längenprüfung nach Land
    country = normalized[:2]
    expected_length = IBAN_LENGTHS.get(country)

    if expected_length and len(normalized) != expected_length:
        return ValidationResult(
            status=ValidationStatus.INVALID,
            field="iban",
            value=value,
            message=f"IBAN hat falsche Länge für {country}: {len(normalized)} statt {expected_length}",
        )

    return ValidationResult(
        status=ValidationStatus.VALID,
        field="iban",
        value=normalized,
        details={"country": country},
    )


# =============================================================================
# BIC-Validierung
# =============================================================================

BIC_PATTERN = r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$"


def validate_bic(value: str | None) -> ValidationResult:
    """
    Prüft BIC/SWIFT-Code Format.

    Args:
        value: Zu prüfender Wert

    Returns:
        ValidationResult
    """
    if not value:
        return ValidationResult(
            status=ValidationStatus.MISSING,
            field="bic",
            message="BIC fehlt",
        )

    normalized = value.strip().upper().replace(" ", "")

    if re.match(BIC_PATTERN, normalized):
        return ValidationResult(
            status=ValidationStatus.VALID,
            field="bic",
            value=normalized,
        )

    return ValidationResult(
        status=ValidationStatus.INVALID,
        field="bic",
        value=value,
        message=f"Ungültiger BIC: {value}",
    )


# =============================================================================
# Rechnungsnummer
# =============================================================================

INVOICE_NUMBER_PATTERN = r"^[A-Za-z0-9\-\/\.]{3,50}$"


def validate_invoice_number(value: str | None) -> ValidationResult:
    """
    Prüft ob Rechnungsnummer plausibel ist.

    Args:
        value: Zu prüfender Wert

    Returns:
        ValidationResult
    """
    if not value:
        return ValidationResult(
            status=ValidationStatus.MISSING,
            field="invoice_number",
            message="Rechnungsnummer fehlt",
        )

    normalized = value.strip()

    if re.match(INVOICE_NUMBER_PATTERN, normalized):
        return ValidationResult(
            status=ValidationStatus.VALID,
            field="invoice_number",
            value=normalized,
        )

    return ValidationResult(
        status=ValidationStatus.INVALID,
        field="invoice_number",
        value=value,
        message=f"Ungültiges Rechnungsnummer-Format: {value}",
    )


# =============================================================================
# Datumsvalidierung
# =============================================================================

DATE_FORMATS = [
    "%d.%m.%Y",  # 31.12.2025
    "%d.%m.%y",  # 31.12.25
    "%d/%m/%Y",  # 31/12/2025
    "%d/%m/%y",  # 31/12/25
    "%Y-%m-%d",  # 2025-12-31
    "%d-%m-%Y",  # 31-12-2025
]

MONTH_NAMES_DE = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


def parse_date(value: str) -> date | None:
    """
    Versucht Datum aus verschiedenen Formaten zu parsen.

    Args:
        value: Datums-String

    Returns:
        date oder None
    """
    if not value:
        return None

    clean_value = value.strip()

    # Standard-Formate
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(clean_value, fmt).date()
        except ValueError:
            continue

    # Ausgeschriebene deutsche Monate: "15. Januar 2025"
    pattern = r"(\d{1,2})\.\s*([A-Za-zäöüÄÖÜß]+)\s+(\d{4})"
    match = re.match(pattern, clean_value)
    if match:
        day = int(match.group(1))
        month_name = match.group(2).lower()
        year = int(match.group(3))
        month = MONTH_NAMES_DE.get(month_name)
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    return None


def validate_date(
    value: str | date | None,
    field_name: str = "date",
    max_date: date | None = None,
    min_date: date | None = None,
) -> ValidationResult:
    """
    Validiert ein Datum.

    Args:
        value: Datumswert (String oder date)
        field_name: Feldname für Fehlermeldung
        max_date: Maximales erlaubtes Datum
        min_date: Minimales erlaubtes Datum

    Returns:
        ValidationResult
    """
    if value is None:
        return ValidationResult(
            status=ValidationStatus.MISSING,
            field=field_name,
            message=f"{field_name} fehlt",
        )

    # String parsen
    if isinstance(value, str):
        parsed = parse_date(value)
        if not parsed:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                field=field_name,
                value=value,
                message=f"Ungültiges Datumsformat: {value}",
            )
        value = parsed

    # Bereichsprüfung
    if max_date and value > max_date:
        return ValidationResult(
            status=ValidationStatus.INVALID,
            field=field_name,
            value=value,
            message=f"Datum {value} liegt nach {max_date}",
        )

    if min_date and value < min_date:
        return ValidationResult(
            status=ValidationStatus.INVALID,
            field=field_name,
            value=value,
            message=f"Datum {value} liegt vor {min_date}",
        )

    return ValidationResult(
        status=ValidationStatus.VALID,
        field=field_name,
        value=value,
    )


# =============================================================================
# Betragsvalidierung
# =============================================================================

AMOUNT_PATTERNS_DE = [
    r"^(\d{1,3}(?:\.\d{3})*),(\d{2})\s*€?$",  # 1.234,56 €
    r"^(\d+),(\d{2})\s*€?$",  # 1234,56
]

AMOUNT_PATTERNS_EN = [
    r"^(\d{1,3}(?:,\d{3})*)\.(\d{2})\s*(?:€|EUR)?$",  # 1,234.56 EUR
    r"^(\d+)\.(\d{2})\s*(?:€|EUR)?$",  # 1234.56
]


def parse_amount(value: str, locale: str = "de") -> Decimal | None:
    """
    Parst Geldbetrag aus String.

    Args:
        value: Betrags-String
        locale: Locale ("de" oder "en")

    Returns:
        Decimal oder None
    """
    if not value:
        return None

    patterns = AMOUNT_PATTERNS_DE if locale == "de" else AMOUNT_PATTERNS_EN

    for pattern in patterns:
        match = re.match(pattern, value.strip())
        if match:
            integer_part = match.group(1).replace(".", "").replace(",", "")
            decimal_part = match.group(2)
            return Decimal(f"{integer_part}.{decimal_part}")

    # Fallback: einfaches Parsing
    clean_value = re.sub(r"[€$£\s]", "", value)

    # Deutsche Notation: 1.234,56 -> 1234.56
    if "," in clean_value and "." in clean_value:
        if clean_value.rfind(",") > clean_value.rfind("."):
            clean_value = clean_value.replace(".", "").replace(",", ".")
        else:
            clean_value = clean_value.replace(",", "")
    elif "," in clean_value:
        clean_value = clean_value.replace(",", ".")

    try:
        return Decimal(clean_value)
    except InvalidOperation:
        return None


def validate_amount(
    value: str | Decimal | None,
    field_name: str = "amount",
    min_value: Decimal | None = None,
    max_value: Decimal | None = None,
) -> ValidationResult:
    """
    Validiert einen Geldbetrag.

    Args:
        value: Betragswert
        field_name: Feldname
        min_value: Minimaler Betrag
        max_value: Maximaler Betrag

    Returns:
        ValidationResult
    """
    if value is None:
        return ValidationResult(
            status=ValidationStatus.MISSING,
            field=field_name,
            message=f"{field_name} fehlt",
        )

    if isinstance(value, str):
        parsed = parse_amount(value)
        if parsed is None:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                field=field_name,
                value=value,
                message=f"Ungültiges Betragsformat: {value}",
            )
        value = parsed

    if min_value is not None and value < min_value:
        return ValidationResult(
            status=ValidationStatus.INVALID,
            field=field_name,
            value=value,
            message=f"{field_name} ({value}) ist kleiner als Minimum ({min_value})",
        )

    if max_value is not None and value > max_value:
        return ValidationResult(
            status=ValidationStatus.INVALID,
            field=field_name,
            value=value,
            message=f"{field_name} ({value}) ist größer als Maximum ({max_value})",
        )

    return ValidationResult(
        status=ValidationStatus.VALID,
        field=field_name,
        value=value,
    )


# =============================================================================
# MwSt-Satz Validierung
# =============================================================================

VALID_VAT_RATES = {
    "DE": [19, 7, 0],  # Deutschland
    "AT": [20, 13, 10, 0],  # Österreich
    "FR": [20, 10, 5.5, 2.1, 0],  # Frankreich
    "UK": [20, 5, 0],  # UK
    "EU": [0, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 27],
}


def validate_vat_rate(
    value: int | float | str | None,
    jurisdiction: str = "DE",
) -> ValidationResult:
    """
    Validiert MwSt-Satz.

    Args:
        value: MwSt-Satz (als Prozent, z.B. 19)
        jurisdiction: Rechtsgebiet

    Returns:
        ValidationResult
    """
    if value is None:
        return ValidationResult(
            status=ValidationStatus.MISSING,
            field="vat_rate",
            message="MwSt-Satz fehlt",
        )

    # Zu Zahl konvertieren
    if isinstance(value, str):
        try:
            value = int(re.sub(r"[^\d]", "", value))
        except ValueError:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                field="vat_rate",
                value=value,
                message=f"Ungültiger MwSt-Satz: {value}",
            )

    valid_rates = VALID_VAT_RATES.get(jurisdiction, VALID_VAT_RATES["EU"])

    if value in valid_rates:
        return ValidationResult(
            status=ValidationStatus.VALID,
            field="vat_rate",
            value=value,
        )

    return ValidationResult(
        status=ValidationStatus.WARNING,
        field="vat_rate",
        value=value,
        message=f"Unüblicher MwSt-Satz {value}% für {jurisdiction}",
        details={"valid_rates": valid_rates},
    )


# =============================================================================
# Rechnerische Prüfung (Brutto = Netto + MwSt)
# =============================================================================


def validate_amount_calculation(
    net_amount: Decimal | None,
    vat_amount: Decimal | None,
    gross_amount: Decimal | None,
    vat_rate: int | None = None,
    tolerance: Decimal = Decimal("0.05"),
) -> ValidationResult:
    """
    Prüft rechnerische Konsistenz der Beträge.

    Args:
        net_amount: Nettobetrag
        vat_amount: MwSt-Betrag
        gross_amount: Bruttobetrag
        vat_rate: MwSt-Satz (optional)
        tolerance: Toleranz für Rundungsdifferenzen

    Returns:
        ValidationResult
    """
    missing_fields = []
    if net_amount is None:
        missing_fields.append("net_amount")
    if vat_amount is None:
        missing_fields.append("vat_amount")
    if gross_amount is None:
        missing_fields.append("gross_amount")

    if len(missing_fields) > 1:
        return ValidationResult(
            status=ValidationStatus.MISSING,
            field="amount_calculation",
            message=f"Fehlende Beträge: {', '.join(missing_fields)}",
        )

    # Prüfung: Brutto = Netto + MwSt
    if net_amount and vat_amount and gross_amount:
        expected_gross = net_amount + vat_amount
        diff = abs(expected_gross - gross_amount)

        if diff > tolerance:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                field="amount_calculation",
                message=f"Rechenfehler: {net_amount} + {vat_amount} = {expected_gross}, aber Brutto = {gross_amount}",
                details={
                    "net_amount": str(net_amount),
                    "vat_amount": str(vat_amount),
                    "gross_amount": str(gross_amount),
                    "expected_gross": str(expected_gross),
                    "difference": str(diff),
                },
            )

    # Prüfung: MwSt = Netto * Rate
    if net_amount and vat_amount and vat_rate:
        expected_vat = net_amount * Decimal(vat_rate) / Decimal(100)
        diff = abs(expected_vat - vat_amount)

        if diff > tolerance:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                field="amount_calculation",
                message=f"MwSt-Berechnung: {net_amount} * {vat_rate}% = {expected_vat:.2f}, aber MwSt = {vat_amount}",
                details={
                    "net_amount": str(net_amount),
                    "vat_rate": vat_rate,
                    "vat_amount": str(vat_amount),
                    "expected_vat": str(expected_vat),
                    "difference": str(diff),
                },
            )

    return ValidationResult(
        status=ValidationStatus.VALID,
        field="amount_calculation",
        details={
            "net_amount": str(net_amount) if net_amount else None,
            "vat_amount": str(vat_amount) if vat_amount else None,
            "gross_amount": str(gross_amount) if gross_amount else None,
        },
    )


# =============================================================================
# Kleinbetragsrechnung (§ 33 UStDV)
# =============================================================================

SMALL_AMOUNT_THRESHOLDS = {
    "DE": Decimal("250.00"),  # § 33 UStDV
    "EU": Decimal("400.00"),  # Art. 238 MwSt-Richtlinie
    "UK": Decimal("250.00"),  # HMRC
}


def is_small_amount_invoice(
    gross_amount: Decimal | None,
    jurisdiction: str = "DE",
) -> bool:
    """
    Prüft ob Rechnung unter Kleinbetragsgrenze liegt.

    Args:
        gross_amount: Bruttobetrag
        jurisdiction: Rechtsgebiet

    Returns:
        True wenn Kleinbetragsrechnung
    """
    if gross_amount is None:
        return False

    threshold = SMALL_AMOUNT_THRESHOLDS.get(jurisdiction, Decimal("250.00"))
    return gross_amount <= threshold
