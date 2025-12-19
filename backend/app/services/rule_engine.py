# Pfad: /backend/app/services/rule_engine.py
"""
FlowAudit Rule Engine

Deterministische Vorprüfung nach Ruleset-Spezifikation.
Führt regelbasierte Validierung vor KI-Analyse durch.
"""

import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from app.models.enums import ErrorSourceCategory, Severity, TaxLawErrorType
from app.services.parser import ExtractedValue, ParseResult
from app.services.validators import (
    ValidationResult,
    ValidationStatus,
    is_small_amount_invoice,
    validate_amount,
    validate_amount_calculation,
    validate_bic,
    validate_date,
    validate_eu_vat_id,
    validate_german_tax_id,
    validate_german_vat_id,
    validate_iban,
    validate_invoice_number,
    validate_uk_vat_id,
    validate_vat_rate,
)

logger = logging.getLogger(__name__)


class FeatureCategory(str, Enum):
    """Feature-Kategorie für Statistik."""

    IDENTITY = "IDENTITY"
    DATE = "DATE"
    AMOUNT = "AMOUNT"
    TAX = "TAX"
    TEXT = "TEXT"
    SEMANTIC = "SEMANTIC"
    PROJECT_CONTEXT = "PROJECT_CONTEXT"


class RequiredLevel(str, Enum):
    """Pflichtgrad eines Merkmals."""

    REQUIRED = "REQUIRED"
    CONDITIONAL = "CONDITIONAL"
    OPTIONAL = "OPTIONAL"


@dataclass
class FeatureDefinition:
    """Definition eines steuerlichen Merkmals."""

    feature_id: str
    name_de: str
    name_en: str
    legal_basis: str
    required_level: RequiredLevel
    category: FeatureCategory
    validation_func: str | None = None


@dataclass
class FeatureCheck:
    """Ergebnis einer Feature-Prüfung."""

    feature_id: str
    status: ValidationStatus
    value: Any = None
    raw_text: str = ""
    error_type: TaxLawErrorType | None = None
    error_source: ErrorSourceCategory = ErrorSourceCategory.TAX_LAW
    severity: Severity = Severity.LOW
    message: str = ""
    legal_basis: str = ""


@dataclass
class PrecheckResult:
    """Ergebnis der deterministischen Vorprüfung."""

    ruleset_id: str
    is_small_amount: bool
    checks: list[FeatureCheck] = field(default_factory=list)
    errors: list[FeatureCheck] = field(default_factory=list)
    warnings: list[FeatureCheck] = field(default_factory=list)
    passed: bool = True


# =============================================================================
# Ruleset-Definitionen
# =============================================================================

DE_USTG_FEATURES: dict[str, FeatureDefinition] = {
    "invoice_number": FeatureDefinition(
        feature_id="invoice_number",
        name_de="Rechnungsnummer",
        name_en="Invoice number",
        legal_basis="§ 14 Abs. 4 Nr. 4 UStG",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.IDENTITY,
        validation_func="validate_invoice_number",
    ),
    "invoice_date": FeatureDefinition(
        feature_id="invoice_date",
        name_de="Rechnungsdatum",
        name_en="Invoice date",
        legal_basis="§ 14 Abs. 4 Nr. 3 UStG",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.DATE,
        validation_func="validate_date",
    ),
    "supplier_name_address": FeatureDefinition(
        feature_id="supplier_name_address",
        name_de="Name und Anschrift des leistenden Unternehmers",
        name_en="Supplier name and address",
        legal_basis="§ 14 Abs. 4 Nr. 1 UStG",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.TEXT,
    ),
    "customer_name_address": FeatureDefinition(
        feature_id="customer_name_address",
        name_de="Name und Anschrift des Leistungsempfängers",
        name_en="Customer name and address",
        legal_basis="§ 14 Abs. 4 Nr. 1 UStG",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.TEXT,
    ),
    "tax_number": FeatureDefinition(
        feature_id="tax_number",
        name_de="Steuernummer",
        name_en="Tax number",
        legal_basis="§ 14 Abs. 4 Nr. 2 UStG",
        required_level=RequiredLevel.CONDITIONAL,
        category=FeatureCategory.TAX,
        validation_func="validate_german_tax_id",
    ),
    "vat_id": FeatureDefinition(
        feature_id="vat_id",
        name_de="USt-IdNr.",
        name_en="VAT ID",
        legal_basis="§ 14 Abs. 4 Nr. 2 UStG",
        required_level=RequiredLevel.CONDITIONAL,
        category=FeatureCategory.TAX,
        validation_func="validate_german_vat_id",
    ),
    "supply_description": FeatureDefinition(
        feature_id="supply_description",
        name_de="Art und Umfang der Leistung",
        name_en="Description of supply",
        legal_basis="§ 14 Abs. 4 Nr. 5 UStG",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.TEXT,
    ),
    "supply_date_or_period": FeatureDefinition(
        feature_id="supply_date_or_period",
        name_de="Leistungszeitpunkt oder -zeitraum",
        name_en="Date of supply",
        legal_basis="§ 14 Abs. 4 Nr. 6 UStG",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.DATE,
    ),
    "net_amount": FeatureDefinition(
        feature_id="net_amount",
        name_de="Nettobetrag",
        name_en="Net amount",
        legal_basis="§ 14 Abs. 4 Nr. 7 UStG",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.AMOUNT,
        validation_func="validate_amount",
    ),
    "vat_rate": FeatureDefinition(
        feature_id="vat_rate",
        name_de="Steuersatz",
        name_en="VAT rate",
        legal_basis="§ 14 Abs. 4 Nr. 8 UStG",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.TAX,
        validation_func="validate_vat_rate",
    ),
    "vat_amount": FeatureDefinition(
        feature_id="vat_amount",
        name_de="Steuerbetrag",
        name_en="VAT amount",
        legal_basis="§ 14 Abs. 4 Nr. 8 UStG",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.AMOUNT,
        validation_func="validate_amount",
    ),
    "gross_amount": FeatureDefinition(
        feature_id="gross_amount",
        name_de="Bruttobetrag",
        name_en="Gross amount",
        legal_basis="§ 14 Abs. 4 UStG",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.AMOUNT,
        validation_func="validate_amount",
    ),
    "iban": FeatureDefinition(
        feature_id="iban",
        name_de="IBAN",
        name_en="IBAN",
        legal_basis="",
        required_level=RequiredLevel.OPTIONAL,
        category=FeatureCategory.IDENTITY,
        validation_func="validate_iban",
    ),
    "bic": FeatureDefinition(
        feature_id="bic",
        name_de="BIC",
        name_en="BIC",
        legal_basis="",
        required_level=RequiredLevel.OPTIONAL,
        category=FeatureCategory.IDENTITY,
        validation_func="validate_bic",
    ),
}

# Reduzierte Pflichtfelder für Kleinbetragsrechnungen (§ 33 UStDV)
DE_SMALL_AMOUNT_REQUIRED = {
    "supplier_name_address",
    "invoice_date",
    "supply_description",
    "gross_amount",
    "vat_rate",
}


EU_VAT_FEATURES: dict[str, FeatureDefinition] = {
    "invoice_number": FeatureDefinition(
        feature_id="invoice_number",
        name_de="Fortlaufende Nummer",
        name_en="Sequential number",
        legal_basis="Art. 226 Nr. 2 MwSt-RL",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.IDENTITY,
        validation_func="validate_invoice_number",
    ),
    "invoice_date": FeatureDefinition(
        feature_id="invoice_date",
        name_de="Rechnungsdatum",
        name_en="Date of issue",
        legal_basis="Art. 226 Nr. 1 MwSt-RL",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.DATE,
        validation_func="validate_date",
    ),
    "supplier_vat_id": FeatureDefinition(
        feature_id="supplier_vat_id",
        name_de="USt-ID des Lieferanten",
        name_en="Supplier VAT ID",
        legal_basis="Art. 226 Nr. 3 MwSt-RL",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.TAX,
        validation_func="validate_eu_vat_id",
    ),
    "customer_vat_id": FeatureDefinition(
        feature_id="customer_vat_id",
        name_de="USt-ID des Kunden",
        name_en="Customer VAT ID",
        legal_basis="Art. 226 Nr. 4 MwSt-RL",
        required_level=RequiredLevel.CONDITIONAL,
        category=FeatureCategory.TAX,
        validation_func="validate_eu_vat_id",
    ),
    "reverse_charge_notice": FeatureDefinition(
        feature_id="reverse_charge_notice",
        name_de="Reverse-Charge-Hinweis",
        name_en="Reverse charge notice",
        legal_basis="Art. 226 Nr. 11a MwSt-RL",
        required_level=RequiredLevel.CONDITIONAL,
        category=FeatureCategory.TEXT,
    ),
}


UK_VAT_FEATURES: dict[str, FeatureDefinition] = {
    "invoice_number": FeatureDefinition(
        feature_id="invoice_number",
        name_de="Eindeutige Nummer",
        name_en="Unique identifying number",
        legal_basis="VAT Notice 700",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.IDENTITY,
        validation_func="validate_invoice_number",
    ),
    "invoice_date": FeatureDefinition(
        feature_id="invoice_date",
        name_de="Rechnungsdatum",
        name_en="Date of issue",
        legal_basis="VAT Notice 700",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.DATE,
        validation_func="validate_date",
    ),
    "supplier_vat_number": FeatureDefinition(
        feature_id="supplier_vat_number",
        name_de="VAT-Nummer des Lieferanten",
        name_en="Supplier VAT registration number",
        legal_basis="VAT Notice 700",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.TAX,
        validation_func="validate_uk_vat_id",
    ),
    "tax_point": FeatureDefinition(
        feature_id="tax_point",
        name_de="Steuerzeitpunkt",
        name_en="Time of supply (tax point)",
        legal_basis="VAT Notice 700",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.DATE,
    ),
    "unit_price": FeatureDefinition(
        feature_id="unit_price",
        name_de="Einzelpreis",
        name_en="Unit price excluding VAT",
        legal_basis="VAT Notice 700",
        required_level=RequiredLevel.REQUIRED,
        category=FeatureCategory.AMOUNT,
        validation_func="validate_amount",
    ),
}


RULESETS = {
    "DE_USTG": DE_USTG_FEATURES,
    "EU_VAT": EU_VAT_FEATURES,
    "UK_VAT": UK_VAT_FEATURES,
}


# =============================================================================
# Rule Engine
# =============================================================================


class RuleEngine:
    """
    Deterministische Regel-Engine für Vorprüfung.

    Prüft extrahierte Daten gegen Ruleset-Definitionen
    bevor KI-Analyse durchgeführt wird.
    """

    def __init__(self, ruleset_id: str = "DE_USTG"):
        """
        Initialisiert Rule Engine.

        Args:
            ruleset_id: Ruleset-ID (DE_USTG, EU_VAT, UK_VAT)
        """
        self.ruleset_id = ruleset_id
        self.features = RULESETS.get(ruleset_id, DE_USTG_FEATURES)

    def precheck(
        self,
        parse_result: ParseResult,
        project_start: date | None = None,
        project_end: date | None = None,
    ) -> PrecheckResult:
        """
        Führt deterministische Vorprüfung durch.

        Args:
            parse_result: Ergebnis des PDF-Parsings
            project_start: Projektbeginn (optional)
            project_end: Projektende (optional)

        Returns:
            PrecheckResult mit allen Prüfergebnissen
        """
        extracted = parse_result.extracted
        checks: list[FeatureCheck] = []
        errors: list[FeatureCheck] = []
        warnings: list[FeatureCheck] = []

        # Bruttobetrag für Kleinbetragslogik
        gross_value = self._get_decimal_value(extracted.get("gross_amount"))
        is_small = is_small_amount_invoice(gross_value, self.ruleset_id[:2])

        # Pflichtfelder bestimmen
        required_features = self._get_required_features(is_small)

        # Einzelprüfungen durchführen
        for feature_id, feature_def in self.features.items():
            check = self._check_feature(
                feature_id,
                feature_def,
                extracted,
                required_features,
                project_start,
                project_end,
            )
            checks.append(check)

            if check.status == ValidationStatus.INVALID:
                errors.append(check)
            elif check.status == ValidationStatus.WARNING:
                warnings.append(check)
            elif check.status == ValidationStatus.MISSING and feature_id in required_features:
                errors.append(check)

        # Rechnerische Prüfung
        calc_check = self._check_calculation(extracted)
        checks.append(calc_check)
        if calc_check.status == ValidationStatus.INVALID:
            errors.append(calc_check)
        elif calc_check.status == ValidationStatus.WARNING:
            warnings.append(calc_check)

        # Steuernummer/USt-ID Prüfung (mindestens eins muss vorhanden sein)
        if self.ruleset_id == "DE_USTG" and not is_small:
            tax_check = self._check_tax_identification(extracted)
            checks.append(tax_check)
            if tax_check.status == ValidationStatus.MISSING:
                errors.append(tax_check)

        # Projektzeitraum-Prüfung (Leistungsdatum im Projektzeitraum)
        if project_start or project_end:
            period_check = self._check_supply_date_in_project_period(
                extracted, project_start, project_end
            )
            checks.append(period_check)
            if period_check.status == ValidationStatus.INVALID:
                errors.append(period_check)
            elif period_check.status == ValidationStatus.WARNING:
                warnings.append(period_check)

        return PrecheckResult(
            ruleset_id=self.ruleset_id,
            is_small_amount=is_small,
            checks=checks,
            errors=errors,
            warnings=warnings,
            passed=len(errors) == 0,
        )

    def _get_required_features(self, is_small_amount: bool) -> set[str]:
        """
        Bestimmt Pflichtfelder basierend auf Rechnungstyp.

        Args:
            is_small_amount: Ob Kleinbetragsrechnung

        Returns:
            Set der Pflichtfeld-IDs
        """
        if self.ruleset_id == "DE_USTG" and is_small_amount:
            return DE_SMALL_AMOUNT_REQUIRED

        return {
            fid
            for fid, fdef in self.features.items()
            if fdef.required_level == RequiredLevel.REQUIRED
        }

    def _check_feature(
        self,
        feature_id: str,
        feature_def: FeatureDefinition,
        extracted: dict[str, ExtractedValue],
        required_features: set[str],
        project_start: date | None,
        project_end: date | None,
    ) -> FeatureCheck:
        """
        Prüft einzelnes Feature.

        Args:
            feature_id: Feature-ID
            feature_def: Feature-Definition
            extracted: Extrahierte Daten
            required_features: Pflichtfelder
            project_start: Projektbeginn
            project_end: Projektende

        Returns:
            FeatureCheck
        """
        extracted_value = extracted.get(feature_id)
        is_required = feature_id in required_features

        # Wert nicht vorhanden
        if not extracted_value or not extracted_value.value:
            if is_required:
                return FeatureCheck(
                    feature_id=feature_id,
                    status=ValidationStatus.MISSING,
                    error_type=TaxLawErrorType.MISSING,
                    error_source=ErrorSourceCategory.TAX_LAW,
                    severity=Severity.HIGH,
                    message=f"{feature_def.name_de} fehlt",
                    legal_basis=feature_def.legal_basis,
                )
            return FeatureCheck(
                feature_id=feature_id,
                status=ValidationStatus.MISSING,
                message=f"{feature_def.name_de} nicht gefunden (optional)",
                legal_basis=feature_def.legal_basis,
            )

        value = extracted_value.value
        raw_text = extracted_value.raw_text

        # Spezifische Validierung
        validation_result = self._run_validation(
            feature_id,
            feature_def,
            value,
            project_start,
            project_end,
        )

        if validation_result:
            error_type = self._map_to_error_type(validation_result.status, feature_def.category)
            severity = self._calculate_severity(validation_result.status, is_required)

            return FeatureCheck(
                feature_id=feature_id,
                status=validation_result.status,
                value=value,
                raw_text=raw_text,
                error_type=error_type if validation_result.status != ValidationStatus.VALID else None,
                error_source=ErrorSourceCategory.TAX_LAW,
                severity=severity,
                message=validation_result.message,
                legal_basis=feature_def.legal_basis,
            )

        # Ohne spezifische Validierung: Wert vorhanden = OK
        return FeatureCheck(
            feature_id=feature_id,
            status=ValidationStatus.VALID,
            value=value,
            raw_text=raw_text,
            legal_basis=feature_def.legal_basis,
        )

    def _run_validation(
        self,
        feature_id: str,
        feature_def: FeatureDefinition,
        value: Any,
        project_start: date | None,
        project_end: date | None,
    ) -> ValidationResult | None:
        """
        Führt spezifische Validierung durch.

        Args:
            feature_id: Feature-ID
            feature_def: Feature-Definition
            value: Zu prüfender Wert
            project_start: Projektbeginn
            project_end: Projektende

        Returns:
            ValidationResult oder None
        """
        func_name = feature_def.validation_func
        if not func_name:
            return None

        # Datumsvalidierung mit Projektkontext
        if func_name == "validate_date":
            max_date = date.today()
            return validate_date(value, feature_id, max_date=max_date)

        # Betragsvalidierung
        if func_name == "validate_amount":
            min_val = Decimal("0.01") if "amount" in feature_id else None
            return validate_amount(value, feature_id, min_value=min_val)

        # MwSt-Satz
        if func_name == "validate_vat_rate":
            jurisdiction = self.ruleset_id[:2]
            return validate_vat_rate(value, jurisdiction)

        # Tax IDs
        if func_name == "validate_german_tax_id":
            return validate_german_tax_id(value)

        if func_name == "validate_german_vat_id":
            return validate_german_vat_id(value)

        if func_name == "validate_eu_vat_id":
            return validate_eu_vat_id(value)

        if func_name == "validate_uk_vat_id":
            return validate_uk_vat_id(value)

        # Sonstige
        if func_name == "validate_invoice_number":
            return validate_invoice_number(value)

        if func_name == "validate_iban":
            return validate_iban(value)

        if func_name == "validate_bic":
            return validate_bic(value)

        return None

    def _check_calculation(
        self,
        extracted: dict[str, ExtractedValue],
    ) -> FeatureCheck:
        """
        Prüft rechnerische Konsistenz.

        Args:
            extracted: Extrahierte Daten

        Returns:
            FeatureCheck
        """
        net = self._get_decimal_value(extracted.get("net_amount"))
        vat = self._get_decimal_value(extracted.get("vat_amount"))
        gross = self._get_decimal_value(extracted.get("gross_amount"))
        rate = self._get_int_value(extracted.get("vat_rate"))

        result = validate_amount_calculation(net, vat, gross, rate)

        error_type = None
        if result.status == ValidationStatus.INVALID:
            error_type = TaxLawErrorType.CALCULATION_ERROR

        return FeatureCheck(
            feature_id="amount_calculation",
            status=result.status,
            error_type=error_type,
            error_source=ErrorSourceCategory.TAX_LAW,
            severity=Severity.HIGH if result.status == ValidationStatus.INVALID else Severity.LOW,
            message=result.message,
            legal_basis="§ 14 Abs. 4 UStG",
        )

    def _check_tax_identification(
        self,
        extracted: dict[str, ExtractedValue],
    ) -> FeatureCheck:
        """
        Prüft ob Steuernummer oder USt-ID vorhanden.

        Args:
            extracted: Extrahierte Daten

        Returns:
            FeatureCheck
        """
        has_tax_number = extracted.get("tax_number") and extracted["tax_number"].value
        has_vat_id = extracted.get("vat_id") and extracted["vat_id"].value

        if has_tax_number or has_vat_id:
            return FeatureCheck(
                feature_id="tax_identification",
                status=ValidationStatus.VALID,
                message="Steuernummer oder USt-ID vorhanden",
                legal_basis="§ 14 Abs. 4 Nr. 2 UStG",
            )

        return FeatureCheck(
            feature_id="tax_identification",
            status=ValidationStatus.MISSING,
            error_type=TaxLawErrorType.MISSING,
            error_source=ErrorSourceCategory.TAX_LAW,
            severity=Severity.HIGH,
            message="Weder Steuernummer noch USt-ID vorhanden",
            legal_basis="§ 14 Abs. 4 Nr. 2 UStG",
        )

    def _check_supply_date_in_project_period(
        self,
        extracted: dict[str, ExtractedValue],
        project_start: date | None,
        project_end: date | None,
    ) -> FeatureCheck:
        """
        Prüft ob Leistungsdatum im Projektzeitraum liegt.

        Args:
            extracted: Extrahierte Daten
            project_start: Projektbeginn
            project_end: Projektende

        Returns:
            FeatureCheck
        """
        supply_value = extracted.get("supply_date_or_period")

        # Kein Leistungsdatum vorhanden
        if not supply_value or not supply_value.value:
            return FeatureCheck(
                feature_id="supply_date_in_project_period",
                status=ValidationStatus.WARNING,
                error_source=ErrorSourceCategory.PROJECT_CONTEXT,
                severity=Severity.MEDIUM,
                message="Leistungsdatum nicht vorhanden - Projektzeitraum-Prüfung nicht möglich",
            )

        # Leistungsdatum parsen
        supply_date = self._parse_date_value(supply_value.value)

        if not supply_date:
            return FeatureCheck(
                feature_id="supply_date_in_project_period",
                status=ValidationStatus.WARNING,
                error_source=ErrorSourceCategory.PROJECT_CONTEXT,
                severity=Severity.MEDIUM,
                message="Leistungsdatum konnte nicht geparst werden - Projektzeitraum-Prüfung nicht möglich",
            )

        # Prüfung gegen Projektzeitraum
        errors: list[str] = []

        if project_start and supply_date < project_start:
            errors.append(
                f"Leistungsdatum ({supply_date.strftime('%d.%m.%Y')}) "
                f"liegt vor Projektbeginn ({project_start.strftime('%d.%m.%Y')})"
            )

        if project_end and supply_date > project_end:
            errors.append(
                f"Leistungsdatum ({supply_date.strftime('%d.%m.%Y')}) "
                f"liegt nach Projektende ({project_end.strftime('%d.%m.%Y')})"
            )

        if errors:
            return FeatureCheck(
                feature_id="supply_date_in_project_period",
                status=ValidationStatus.INVALID,
                value=supply_date,
                raw_text=supply_value.raw_text,
                error_type=TaxLawErrorType.DATE_INVALID,
                error_source=ErrorSourceCategory.PROJECT_CONTEXT,
                severity=Severity.HIGH,
                message="; ".join(errors),
            )

        return FeatureCheck(
            feature_id="supply_date_in_project_period",
            status=ValidationStatus.VALID,
            value=supply_date,
            raw_text=supply_value.raw_text,
            message="Leistungsdatum liegt im Projektzeitraum",
        )

    def _parse_date_value(self, value: Any) -> date | None:
        """
        Parst Datumswert aus verschiedenen Formaten.

        Args:
            value: Datumswert (date, datetime, str)

        Returns:
            date oder None
        """
        if isinstance(value, date):
            return value

        if isinstance(value, str):
            # Verschiedene Datumsformate versuchen
            formats = [
                "%Y-%m-%d",      # ISO
                "%d.%m.%Y",      # DE
                "%d/%m/%Y",      # EU
                "%m/%d/%Y",      # US
                "%Y%m%d",        # Kompakt
            ]
            for fmt in formats:
                try:
                    from datetime import datetime
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue

        return None

    def _get_decimal_value(self, extracted: ExtractedValue | None) -> Decimal | None:
        """Extrahiert Decimal-Wert."""
        if not extracted or not extracted.value:
            return None
        if isinstance(extracted.value, Decimal):
            return extracted.value
        try:
            return Decimal(str(extracted.value))
        except Exception:
            return None

    def _get_int_value(self, extracted: ExtractedValue | None) -> int | None:
        """Extrahiert Int-Wert."""
        if not extracted or not extracted.value:
            return None
        if isinstance(extracted.value, int):
            return extracted.value
        try:
            return int(extracted.value)
        except Exception:
            return None

    def _map_to_error_type(
        self,
        status: ValidationStatus,
        category: FeatureCategory,
    ) -> TaxLawErrorType | None:
        """Mappt Validierungsstatus auf TaxLawErrorType."""
        if status == ValidationStatus.VALID:
            return None

        if status == ValidationStatus.MISSING:
            return TaxLawErrorType.MISSING

        if status == ValidationStatus.INVALID:
            if category == FeatureCategory.DATE:
                return TaxLawErrorType.DATE_INVALID
            if category == FeatureCategory.AMOUNT:
                return TaxLawErrorType.CALCULATION_ERROR
            return TaxLawErrorType.WRONG_FORMAT

        return None

    def _calculate_severity(
        self,
        status: ValidationStatus,
        is_required: bool,
    ) -> Severity:
        """Berechnet Schweregrad."""
        if status == ValidationStatus.VALID:
            return Severity.LOW

        if status == ValidationStatus.MISSING:
            return Severity.HIGH if is_required else Severity.LOW

        if status == ValidationStatus.INVALID:
            return Severity.HIGH if is_required else Severity.MEDIUM

        return Severity.MEDIUM


# =============================================================================
# Singleton
# =============================================================================

_engines: dict[str, RuleEngine] = {}


def get_rule_engine(ruleset_id: str = "DE_USTG") -> RuleEngine:
    """
    Gibt Rule-Engine-Instanz zurück.

    Args:
        ruleset_id: Ruleset-ID

    Returns:
        RuleEngine-Instanz
    """
    if ruleset_id not in _engines:
        _engines[ruleset_id] = RuleEngine(ruleset_id)
    return _engines[ruleset_id]
