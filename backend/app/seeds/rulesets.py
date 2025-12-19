# Pfad: /backend/app/seeds/rulesets.py
"""
FlowAudit Ruleset Seed Data

Initialdaten fuer die steuerlichen Regelwerke (DE_USTG, EU_VAT, UK_VAT).
Basierend auf docs/rulesets.md
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ruleset import Ruleset

logger = logging.getLogger(__name__)


# =============================================================================
# DE_USTG - Deutsches Umsatzsteuergesetz
# =============================================================================

DE_USTG_RULESET = {
    "ruleset_id": "DE_USTG",
    "version": "1.0.0",
    "jurisdiction": "DE",
    "title_de": "Deutschland - Umsatzsteuergesetz",
    "title_en": "Germany - VAT Act",
    "default_language": "de",
    "supported_ui_languages": ["de", "en"],
    "currency_default": "EUR",
    "supported_document_types": ["INVOICE"],  # Nur Rechnungen werden geprüft
    "legal_references": [
        {
            "law": "UStG",
            "section": "§ 14 Abs. 4",
            "description_de": "Pflichtangaben in Rechnungen",
            "description_en": "Mandatory invoice fields",
        },
        {
            "law": "UStG",
            "section": "§ 15",
            "description_de": "Vorsteuerabzug",
            "description_en": "Input tax deduction",
        },
        {
            "law": "UStDV",
            "section": "§ 33",
            "description_de": "Kleinbetragsrechnungen",
            "description_en": "Small amount invoices",
        },
        {
            "law": "BHO/LHO",
            "section": "§ 7",
            "description_de": "Wirtschaftlichkeit und Sparsamkeit",
            "description_en": "Economic efficiency",
        },
    ],
    "features": [
        {
            "feature_id": "supplier_name_address",
            "name_de": "Name und Anschrift des leistenden Unternehmers",
            "name_en": "Supplier name and address",
            "legal_basis": "§ 14 Abs. 4 Nr. 1 UStG",
            "required_level": "REQUIRED",
            "extraction_type": "TEXTBLOCK",
            "category": "IDENTITY",
            "explanation_de": "Vollstaendiger Name und Anschrift des Rechnungsausstellers (Leistender). Muss Strasse, Hausnummer, PLZ und Ort enthalten.",
            "explanation_en": "Complete name and address of the invoice issuer (supplier). Must include street, house number, postal code and city.",
            "semantic_meaning_de": "Identifikation des leistenden Unternehmers",
            "semantic_meaning_en": "Identification of the supplying business",
            "validation": {
                "min_length": 10,
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "incomplete_address", "wrong_format"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "customer_name_address",
            "name_de": "Name und Anschrift des Leistungsempfaengers",
            "name_en": "Customer name and address",
            "legal_basis": "§ 14 Abs. 4 Nr. 1 UStG",
            "required_level": "REQUIRED",
            "extraction_type": "TEXTBLOCK",
            "category": "IDENTITY",
            "explanation_de": "Vollstaendiger Name und Anschrift des Rechnungsempfaengers. Bei Zuwendungen muss dieser mit dem Beguenstigten uebereinstimmen.",
            "explanation_en": "Complete name and address of the invoice recipient. For grants, this must match the beneficiary.",
            "semantic_meaning_de": "Zuwendungsempfaenger muss Rechnungsempfaenger sein",
            "semantic_meaning_en": "Grant recipient must be invoice recipient",
            "validation": {
                "min_length": 10,
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "wrong_recipient", "alias_mismatch"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "tax_number",
            "name_de": "Steuernummer des Leistenden",
            "name_en": "Supplier tax number",
            "legal_basis": "§ 14 Abs. 4 Nr. 2 UStG",
            "required_level": "CONDITIONAL",
            "extraction_type": "STRING",
            "category": "TAX",
            "condition": "Erforderlich wenn keine USt-IdNr. angegeben",
            "explanation_de": "Steuernummer des leistenden Unternehmers. Alternativ zur USt-IdNr. Mindestens eine von beiden muss angegeben sein.",
            "explanation_en": "Tax number of the supplier. Alternative to VAT ID. At least one must be provided.",
            "semantic_meaning_de": "Steuerliche Identifikation des Leistenden",
            "semantic_meaning_en": "Tax identification of the supplier",
            "validation": {
                "pattern": "GERMAN_TAX_ID",
                "regex": r"^\d{2,3}[\/\s]?\d{3,4}[\/\s]?\d{4,5}$",
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "wrong_format", "invalid_checksum"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "vat_id",
            "name_de": "Umsatzsteuer-Identifikationsnummer",
            "name_en": "VAT identification number",
            "legal_basis": "§ 14 Abs. 4 Nr. 2 UStG",
            "required_level": "CONDITIONAL",
            "extraction_type": "STRING",
            "category": "TAX",
            "condition": "Erforderlich wenn keine Steuernummer angegeben",
            "explanation_de": "USt-IdNr. des leistenden Unternehmers. Alternativ zur Steuernummer. Bei innergemeinschaftlichen Lieferungen zwingend.",
            "explanation_en": "VAT ID of the supplier. Alternative to tax number. Mandatory for intra-community supplies.",
            "semantic_meaning_de": "EU-weite steuerliche Identifikation",
            "semantic_meaning_en": "EU-wide tax identification",
            "validation": {
                "pattern": "GERMAN_VAT_ID",
                "regex": r"^DE\s?\d{9}$",
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "wrong_country", "wrong_format"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "invoice_date",
            "name_de": "Rechnungsdatum",
            "name_en": "Invoice date",
            "legal_basis": "§ 14 Abs. 4 Nr. 3 UStG",
            "required_level": "REQUIRED",
            "extraction_type": "DATE",
            "category": "DATE",
            "explanation_de": "Ausstellungsdatum der Rechnung. Darf nicht in der Zukunft liegen.",
            "explanation_en": "Date of invoice issuance. Must not be in the future.",
            "semantic_meaning_de": "Zeitpunkt der Rechnungsausstellung",
            "semantic_meaning_en": "Time of invoice issuance",
            "validation": {
                "pattern": "DATE",
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "future_date", "invalid_format"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "invoice_number",
            "name_de": "Rechnungsnummer",
            "name_en": "Invoice number",
            "legal_basis": "§ 14 Abs. 4 Nr. 4 UStG",
            "required_level": "REQUIRED",
            "extraction_type": "STRING",
            "category": "IDENTITY",
            "explanation_de": "Fortlaufende, einmalig vergebene Nummer zur eindeutigen Identifikation der Rechnung.",
            "explanation_en": "Sequential, uniquely assigned number for unique invoice identification.",
            "semantic_meaning_de": "Eindeutige Identifikation der Rechnung",
            "semantic_meaning_en": "Unique identification of the invoice",
            "validation": {
                "regex": r"^[A-Za-z0-9\-\/\.]+$",
                "min_length": 1,
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "duplicate", "non_unique"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "supply_description",
            "name_de": "Art und Umfang der Leistung",
            "name_en": "Description of supply",
            "legal_basis": "§ 14 Abs. 4 Nr. 5 UStG",
            "required_level": "REQUIRED",
            "extraction_type": "TEXTBLOCK",
            "category": "TEXT",
            "explanation_de": "Handels- oder verkehrsuebliche Bezeichnung der gelieferten Gegenstaende oder Art und Umfang der Dienstleistung.",
            "explanation_en": "Commercial description of delivered goods or nature and scope of services.",
            "semantic_meaning_de": "Inhaltliche Beschreibung der erbrachten Leistung",
            "semantic_meaning_en": "Content description of the service provided",
            "validation": {
                "min_length": 3,
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "too_vague", "not_matching_project"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "supply_date_or_period",
            "name_de": "Leistungszeitpunkt oder -zeitraum",
            "name_en": "Date or period of supply",
            "legal_basis": "§ 14 Abs. 4 Nr. 6 UStG",
            "required_level": "REQUIRED",
            "extraction_type": "DATE_OR_RANGE",
            "category": "DATE",
            "explanation_de": "Zeitpunkt oder Zeitraum der Lieferung oder sonstigen Leistung. Bei Zuwendungen muss dies im Projektzeitraum liegen.",
            "explanation_en": "Time or period of delivery or service. For grants, must be within project period.",
            "semantic_meaning_de": "Zeitliche Zuordnung der Leistung zum Projekt",
            "semantic_meaning_en": "Temporal assignment of service to project",
            "validation": {
                "pattern": "DATE_OR_RANGE",
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "outside_project_period", "invalid_format"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "net_amount",
            "name_de": "Nettobetrag (Entgelt)",
            "name_en": "Net amount",
            "legal_basis": "§ 14 Abs. 4 Nr. 7 UStG",
            "required_level": "REQUIRED",
            "extraction_type": "MONEY",
            "category": "AMOUNT",
            "explanation_de": "Nach Steuersaetzen aufgeschluesseltes Entgelt ohne Umsatzsteuer.",
            "explanation_en": "Consideration broken down by tax rates, excluding VAT.",
            "semantic_meaning_de": "Bemessungsgrundlage fuer die Umsatzsteuer",
            "semantic_meaning_en": "Tax base for VAT",
            "validation": {
                "pattern": "MONEY",
                "min_value": 0.01,
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "wrong_calculation", "negative_value"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "vat_rate",
            "name_de": "Steuersatz",
            "name_en": "VAT rate",
            "legal_basis": "§ 14 Abs. 4 Nr. 8 UStG",
            "required_level": "REQUIRED",
            "extraction_type": "PERCENTAGE",
            "category": "TAX",
            "explanation_de": "Anzuwendender Steuersatz (19% oder 7% in Deutschland). Bei Steuerbefreiung entsprechender Hinweis.",
            "explanation_en": "Applicable tax rate (19% or 7% in Germany). For tax exemptions, corresponding notice required.",
            "semantic_meaning_de": "Hoehe der Umsatzsteuerbelastung",
            "semantic_meaning_en": "Amount of VAT burden",
            "validation": {
                "pattern": "VAT_RATE",
                "valid_values": [0, 7, 19],
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "wrong_rate", "inconsistent_with_amount"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "vat_amount",
            "name_de": "Steuerbetrag",
            "name_en": "VAT amount",
            "legal_basis": "§ 14 Abs. 4 Nr. 8 UStG",
            "required_level": "REQUIRED",
            "extraction_type": "MONEY",
            "category": "AMOUNT",
            "explanation_de": "Auf das Entgelt entfallender Steuerbetrag. Muss rechnerisch korrekt sein (Netto x Steuersatz).",
            "explanation_en": "Tax amount on the consideration. Must be mathematically correct (Net x VAT rate).",
            "semantic_meaning_de": "Umsatzsteuerbetrag zur Geltendmachung des Vorsteuerabzugs",
            "semantic_meaning_en": "VAT amount for claiming input tax deduction",
            "validation": {
                "pattern": "MONEY",
                "min_value": 0,
                "tolerance": 0.05,
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "calculation_error", "rounding_error"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "gross_amount",
            "name_de": "Bruttobetrag (Gesamtbetrag)",
            "name_en": "Gross amount (Total)",
            "legal_basis": "§ 14 Abs. 4 UStG",
            "required_level": "REQUIRED",
            "extraction_type": "MONEY",
            "category": "AMOUNT",
            "explanation_de": "Gesamtbetrag inkl. Umsatzsteuer. Muss rechnerisch korrekt sein (Netto + Steuer).",
            "explanation_en": "Total amount including VAT. Must be mathematically correct (Net + VAT).",
            "semantic_meaning_de": "Zu zahlender Gesamtbetrag",
            "semantic_meaning_en": "Total amount payable",
            "validation": {
                "pattern": "MONEY",
                "min_value": 0.01,
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "calculation_error", "mismatch_with_components"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "iban",
            "name_de": "IBAN",
            "name_en": "IBAN",
            "legal_basis": "",
            "required_level": "OPTIONAL",
            "extraction_type": "STRING",
            "category": "IDENTITY",
            "explanation_de": "Internationale Bankkontonummer fuer Zahlungen. Nicht gesetzlich vorgeschrieben, aber ueblich.",
            "explanation_en": "International Bank Account Number for payments. Not legally required, but common.",
            "semantic_meaning_de": "Bankverbindung fuer Zahlungsabwicklung",
            "semantic_meaning_en": "Bank details for payment processing",
            "validation": {
                "pattern": "IBAN",
                "regex": r"^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$",
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["wrong_format", "invalid_country"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "bic",
            "name_de": "BIC",
            "name_en": "BIC",
            "legal_basis": "",
            "required_level": "OPTIONAL",
            "extraction_type": "STRING",
            "category": "IDENTITY",
            "explanation_de": "Bank Identifier Code zur Identifikation der Bank.",
            "explanation_en": "Bank Identifier Code for bank identification.",
            "semantic_meaning_de": "Bankidentifikation",
            "semantic_meaning_en": "Bank identification",
            "validation": {
                "pattern": "BIC",
                "regex": r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$",
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["wrong_format"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
    ],
    "special_rules": {
        "small_amount_threshold_eur": 250.0,
        "small_amount_reduced_fields": [
            "supplier_name_address",
            "invoice_date",
            "supply_description",
            "gross_amount",
            "vat_rate",
        ],
    },
}


# =============================================================================
# EU_VAT - MwSt-Systemrichtlinie
# =============================================================================

EU_VAT_RULESET = {
    "ruleset_id": "EU_VAT",
    "version": "1.0.0",
    "jurisdiction": "EU",
    "title_de": "EU - MwSt-Systemrichtlinie",
    "title_en": "EU - VAT Directive",
    "default_language": "de",
    "supported_ui_languages": ["de", "en"],
    "currency_default": "EUR",
    "supported_document_types": ["INVOICE"],  # Nur Rechnungen werden geprüft
    "legal_references": [
        {
            "law": "MwSt-Systemrichtlinie",
            "section": "Art. 226",
            "description_de": "Pflichtangaben in Rechnungen",
            "description_en": "Mandatory invoice particulars",
        },
        {
            "law": "RL 2006/112/EG",
            "section": "Art. 226-240",
            "description_de": "Rechnungsstellung",
            "description_en": "Invoicing",
        },
    ],
    "features": [
        {
            "feature_id": "invoice_date",
            "name_de": "Ausstellungsdatum",
            "name_en": "Date of issue",
            "legal_basis": "Art. 226 Nr. 1 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "DATE",
            "category": "DATE",
            "explanation_de": "Datum der Rechnungsausstellung.",
            "explanation_en": "Date of invoice issuance.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "invoice_number",
            "name_de": "Fortlaufende Nummer",
            "name_en": "Sequential number",
            "legal_basis": "Art. 226 Nr. 2 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "STRING",
            "category": "IDENTITY",
            "explanation_de": "Fortlaufende Nummer mit einer oder mehreren Zahlenreihen zur eindeutigen Identifikation.",
            "explanation_en": "Sequential number based on one or more series uniquely identifying the invoice.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "supplier_vat_id",
            "name_de": "USt-ID des Lieferanten",
            "name_en": "Supplier VAT ID",
            "legal_basis": "Art. 226 Nr. 3 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "STRING",
            "category": "TAX",
            "explanation_de": "Umsatzsteuer-Identifikationsnummer des leistenden Unternehmers. Keine Alternative durch Steuernummer.",
            "explanation_en": "VAT identification number of the supplier. No alternative through tax number.",
            "validation": {
                "pattern": "EU_VAT_ID",
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "invalid_country", "wrong_format"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "customer_vat_id",
            "name_de": "USt-ID des Kunden (B2B)",
            "name_en": "Customer VAT ID (B2B)",
            "legal_basis": "Art. 226 Nr. 4 MwSt-RL",
            "required_level": "CONDITIONAL",
            "extraction_type": "STRING",
            "category": "TAX",
            "condition": "Erforderlich bei B2B oder innergemeinschaftlicher Lieferung",
            "explanation_de": "USt-IdNr. des Leistungsempfaengers bei B2B-Geschaeften oder innergemeinschaftlichen Lieferungen.",
            "explanation_en": "VAT ID of the customer for B2B transactions or intra-community supplies.",
            "validation": {
                "pattern": "EU_VAT_ID",
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "supplier_name_address",
            "name_de": "Name und Anschrift des Lieferanten",
            "name_en": "Supplier name and address",
            "legal_basis": "Art. 226 Nr. 5 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "TEXTBLOCK",
            "category": "IDENTITY",
            "explanation_de": "Vollstaendiger Name und Anschrift des Rechnungsausstellers.",
            "explanation_en": "Full name and address of the invoice issuer.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "customer_name_address",
            "name_de": "Name und Anschrift des Kunden",
            "name_en": "Customer name and address",
            "legal_basis": "Art. 226 Nr. 6 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "TEXTBLOCK",
            "category": "IDENTITY",
            "explanation_de": "Vollstaendiger Name und Anschrift des Rechnungsempfaengers.",
            "explanation_en": "Full name and address of the invoice recipient.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "supply_description",
            "name_de": "Leistungsbeschreibung",
            "name_en": "Description of goods/services",
            "legal_basis": "Art. 226 Nr. 6 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "TEXTBLOCK",
            "category": "TEXT",
            "explanation_de": "Menge und Art der gelieferten Gegenstaende bzw. Umfang und Art der Dienstleistungen.",
            "explanation_en": "Quantity and nature of goods supplied or extent and nature of services.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "quantity",
            "name_de": "Menge",
            "name_en": "Quantity",
            "legal_basis": "Art. 226 Nr. 6 MwSt-RL",
            "required_level": "CONDITIONAL",
            "extraction_type": "NUMBER",
            "category": "TEXT",
            "condition": "Erforderlich bei Warenlieferungen",
            "explanation_de": "Menge der gelieferten Gegenstaende.",
            "explanation_en": "Quantity of goods delivered.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "supply_date",
            "name_de": "Lieferdatum",
            "name_en": "Date of supply",
            "legal_basis": "Art. 226 Nr. 7 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "DATE",
            "category": "DATE",
            "explanation_de": "Datum der Lieferung oder Leistungserbringung.",
            "explanation_en": "Date of delivery or service provision.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "taxable_amount",
            "name_de": "Bemessungsgrundlage je Steuersatz",
            "name_en": "Taxable amount per rate",
            "legal_basis": "Art. 226 Nr. 8 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "MONEY",
            "category": "AMOUNT",
            "explanation_de": "Steuerbemessungsgrundlage je angewendetem Steuersatz oder je Steuerbefreiung.",
            "explanation_en": "Tax base for each rate applied or exemption.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "unit_price",
            "name_de": "Einzelpreis (netto)",
            "name_en": "Unit price (excl. VAT)",
            "legal_basis": "Art. 226 Nr. 9 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "MONEY",
            "category": "AMOUNT",
            "explanation_de": "Preis je Einheit ohne MwSt sowie Preisminderungen.",
            "explanation_en": "Price per unit excluding VAT and any price reductions.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "vat_rate",
            "name_de": "MwSt-Satz",
            "name_en": "VAT rate",
            "legal_basis": "Art. 226 Nr. 10 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "PERCENTAGE",
            "category": "TAX",
            "explanation_de": "Angewendeter Mehrwertsteuersatz.",
            "explanation_en": "Applied VAT rate.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "vat_amount",
            "name_de": "MwSt-Betrag",
            "name_en": "VAT amount",
            "legal_basis": "Art. 226 Nr. 10 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "MONEY",
            "category": "AMOUNT",
            "explanation_de": "Zu entrichtender MwSt-Betrag (ausser bei Steuerbefreiung).",
            "explanation_en": "VAT amount payable (unless exemption applies).",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "exemption_reason",
            "name_de": "Steuerbefreiungsgrund",
            "name_en": "Exemption reason",
            "legal_basis": "Art. 226 Nr. 11 MwSt-RL",
            "required_level": "CONDITIONAL",
            "extraction_type": "TEXTBLOCK",
            "category": "TAX",
            "condition": "Erforderlich bei Steuerbefreiung",
            "explanation_de": "Hinweis auf Steuerbefreiung mit Angabe der einschlaegigen Bestimmung.",
            "explanation_en": "Reference to exemption with applicable provision.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "reverse_charge_notice",
            "name_de": "Reverse-Charge-Hinweis",
            "name_en": "Reverse charge notice",
            "legal_basis": "Art. 226 Nr. 11a MwSt-RL",
            "required_level": "CONDITIONAL",
            "extraction_type": "TEXTBLOCK",
            "category": "TEXT",
            "condition": "Erforderlich bei Umkehr der Steuerschuldnerschaft",
            "explanation_de": "Hinweis auf Steuerschuldnerschaft des Leistungsempfaengers (Reverse Charge).",
            "explanation_en": "Notice indicating reverse charge applies.",
            "validation": {
                "must_contain_one_of": [
                    "Reverse charge",
                    "Steuerschuldnerschaft des Leistungsempfaengers",
                    "VAT due by the customer",
                ],
            },
            "generator_rules": {
                "can_be_missing": True,
                "typical_errors": ["missing_when_required", "wrong_wording"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "margin_scheme_notice",
            "name_de": "Differenzbesteuerung",
            "name_en": "Margin scheme notice",
            "legal_basis": "Art. 226 Nr. 14 MwSt-RL",
            "required_level": "CONDITIONAL",
            "extraction_type": "TEXTBLOCK",
            "category": "TEXT",
            "condition": "Erforderlich bei Differenzbesteuerung",
            "explanation_de": "Hinweis auf Anwendung einer Sonderregelung (Reisebueros, Gebrauchtwarenhaendler).",
            "explanation_en": "Notice indicating margin scheme applies (travel agents, second-hand goods).",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "gross_amount",
            "name_de": "Gesamtbetrag",
            "name_en": "Total amount",
            "legal_basis": "Art. 226 MwSt-RL",
            "required_level": "REQUIRED",
            "extraction_type": "MONEY",
            "category": "AMOUNT",
            "explanation_de": "Gesamtbetrag der Rechnung inkl. MwSt.",
            "explanation_en": "Total invoice amount including VAT.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
    ],
    "special_rules": {
        "small_amount_threshold_eur": 400.0,
        "small_amount_reduced_fields": [
            "invoice_date",
            "supplier_name_address",
            "supply_description",
            "vat_rate",
            "gross_amount",
        ],
    },
}


# =============================================================================
# UK_VAT - HMRC VAT Notice 700
# =============================================================================

UK_VAT_RULESET = {
    "ruleset_id": "UK_VAT",
    "version": "1.0.0",
    "jurisdiction": "UK",
    "title_de": "UK - VAT Notice 700",
    "title_en": "UK - VAT Notice 700",
    "default_language": "en",
    "supported_ui_languages": ["de", "en"],
    "currency_default": "GBP",
    "supported_document_types": ["INVOICE"],  # Only invoices are checked
    "legal_references": [
        {
            "law": "VAT Act 1994",
            "section": "Schedule 11",
            "description_de": "Rechnungsanforderungen",
            "description_en": "VAT invoice requirements",
        },
        {
            "law": "HMRC VAT Notice 700",
            "section": "Section 16",
            "description_de": "Mehrwertsteuer-Rechnungen",
            "description_en": "VAT invoices",
        },
    ],
    "features": [
        {
            "feature_id": "supplier_name_address",
            "name_de": "Name, Anschrift und VAT-Nummer des Lieferanten",
            "name_en": "Supplier name, address and VAT number",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "TEXTBLOCK",
            "category": "IDENTITY",
            "explanation_de": "Vollstaendiger Name, Anschrift und VAT-Registrierungsnummer des Lieferanten.",
            "explanation_en": "Full name, address and VAT registration number of the supplier.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "supplier_vat_number",
            "name_de": "VAT-Registrierungsnummer des Lieferanten",
            "name_en": "Supplier VAT registration number",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "STRING",
            "category": "TAX",
            "explanation_de": "VAT-Registrierungsnummer des Lieferanten (GB + 9 oder 12 Ziffern).",
            "explanation_en": "VAT registration number of the supplier (GB + 9 or 12 digits).",
            "validation": {
                "pattern": "UK_VAT_ID",
                "regex": r"^GB\s?\d{9}(\d{3})?$",
            },
            "generator_rules": {
                "can_be_missing": True,
                "can_be_malformed": True,
                "typical_errors": ["missing", "wrong_format"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "invoice_number",
            "name_de": "Eindeutige Rechnungsnummer",
            "name_en": "Unique identifying number",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "STRING",
            "category": "IDENTITY",
            "explanation_de": "Eindeutige Nummer zur Identifikation der Rechnung.",
            "explanation_en": "Unique number identifying the invoice.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "invoice_date",
            "name_de": "Rechnungsdatum",
            "name_en": "Date of issue",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "DATE",
            "category": "DATE",
            "explanation_de": "Datum der Rechnungsausstellung.",
            "explanation_en": "Date of invoice issuance.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "tax_point",
            "name_de": "Steuerzeitpunkt (Tax Point)",
            "name_en": "Time of supply (tax point)",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "DATE",
            "category": "DATE",
            "explanation_de": "Zeitpunkt, zu dem die VAT faellig wird. Kann vom Rechnungsdatum abweichen.",
            "explanation_en": "Date when VAT becomes due. May differ from invoice date.",
            "semantic_meaning_de": "Zeitpunkt der Steuerschuld",
            "semantic_meaning_en": "Point at which VAT is due",
            "generator_rules": {
                "can_be_missing": True,
                "typical_errors": ["missing", "different_from_invoice_date_unclear"],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "customer_name_address",
            "name_de": "Name und Anschrift des Kunden",
            "name_en": "Customer name and address",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "TEXTBLOCK",
            "category": "IDENTITY",
            "explanation_de": "Vollstaendiger Name und Anschrift des Rechnungsempfaengers.",
            "explanation_en": "Full name and address of the customer.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "supply_description",
            "name_de": "Beschreibung der Waren/Dienstleistungen",
            "name_en": "Description of goods/services",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "TEXTBLOCK",
            "category": "TEXT",
            "explanation_de": "Beschreibung der gelieferten Waren oder erbrachten Dienstleistungen.",
            "explanation_en": "Description of goods supplied or services rendered.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "quantity",
            "name_de": "Menge",
            "name_en": "Quantity of goods",
            "legal_basis": "VAT Notice 700",
            "required_level": "CONDITIONAL",
            "extraction_type": "NUMBER",
            "category": "TEXT",
            "condition": "Erforderlich bei Warenlieferungen",
            "explanation_de": "Menge der gelieferten Waren.",
            "explanation_en": "Quantity of goods supplied.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "unit_price",
            "name_de": "Einzelpreis (netto)",
            "name_en": "Unit price excluding VAT",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "MONEY",
            "category": "AMOUNT",
            "explanation_de": "Preis je Einheit ohne VAT.",
            "explanation_en": "Price per unit excluding VAT.",
            "validation": {
                "pattern": "MONEY",
                "currency": "GBP",
                "min_value": 0.01,
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "vat_rate",
            "name_de": "VAT-Satz",
            "name_en": "Rate of VAT",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "PERCENTAGE",
            "category": "TAX",
            "explanation_de": "Angewendeter VAT-Satz (20% Standard, 5% ermaessigt, 0% Nullsatz).",
            "explanation_en": "Applied VAT rate (20% standard, 5% reduced, 0% zero-rated).",
            "validation": {
                "valid_values": [0, 5, 20],
            },
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
        {
            "feature_id": "total_excl_vat",
            "name_de": "Gesamtbetrag ohne VAT",
            "name_en": "Total excluding VAT",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "MONEY",
            "category": "AMOUNT",
            "explanation_de": "Gesamtbetrag ohne Mehrwertsteuer.",
            "explanation_en": "Total amount excluding VAT.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "total_vat",
            "name_de": "VAT-Gesamtbetrag",
            "name_en": "Total VAT charged",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "MONEY",
            "category": "AMOUNT",
            "explanation_de": "Gesamter VAT-Betrag der Rechnung.",
            "explanation_en": "Total VAT amount on the invoice.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": False,
            },
        },
        {
            "feature_id": "total_incl_vat",
            "name_de": "Gesamtbetrag inkl. VAT",
            "name_en": "Total amount payable",
            "legal_basis": "VAT Notice 700",
            "required_level": "REQUIRED",
            "extraction_type": "MONEY",
            "category": "AMOUNT",
            "explanation_de": "Zu zahlender Gesamtbetrag inkl. VAT.",
            "explanation_en": "Total amount payable including VAT.",
            "applies_to": {
                "standard_invoice": True,
                "small_amount_invoice": True,
            },
        },
    ],
    "special_rules": {
        "simplified_invoice_threshold_gbp": 250.0,
        "simplified_invoice_fields": [
            "supplier_name_address",
            "supplier_vat_number",
            "invoice_date",
            "supply_description",
            "vat_rate",
            "total_incl_vat",
        ],
    },
}


# =============================================================================
# Seed Function
# =============================================================================

ALL_RULESETS = [DE_USTG_RULESET, EU_VAT_RULESET, UK_VAT_RULESET]


async def seed_rulesets(session: AsyncSession, force: bool = False) -> int:
    """
    Fuegt Standard-Rulesets in die Datenbank ein.

    Args:
        session: Async-Datenbank-Session.
        force: Wenn True, werden bestehende Rulesets ueberschrieben.

    Returns:
        Anzahl der eingefuegten/aktualisierten Rulesets.
    """
    count = 0

    for ruleset_data in ALL_RULESETS:
        ruleset_id = ruleset_data["ruleset_id"]
        version = ruleset_data["version"]

        # Pruefen ob bereits existiert
        result = await session.execute(
            select(Ruleset).where(
                Ruleset.ruleset_id == ruleset_id,
                Ruleset.version == version,
            )
        )
        existing = result.scalar_one_or_none()

        if existing and not force:
            logger.info(f"Ruleset {ruleset_id} v{version} bereits vorhanden, ueberspringe")
            continue

        if existing and force:
            # Update existierendes Ruleset
            existing.title_de = ruleset_data["title_de"]
            existing.title_en = ruleset_data["title_en"]
            existing.legal_references = ruleset_data["legal_references"]
            existing.features = ruleset_data["features"]
            existing.special_rules = ruleset_data.get("special_rules")
            existing.supported_document_types = ruleset_data.get("supported_document_types", ["INVOICE"])
            logger.info(f"Ruleset {ruleset_id} v{version} aktualisiert")
        else:
            # Neues Ruleset erstellen
            ruleset = Ruleset(
                ruleset_id=ruleset_id,
                version=version,
                jurisdiction=ruleset_data["jurisdiction"],
                title_de=ruleset_data["title_de"],
                title_en=ruleset_data["title_en"],
                legal_references=ruleset_data["legal_references"],
                features=ruleset_data["features"],
                default_language=ruleset_data["default_language"],
                supported_ui_languages=ruleset_data["supported_ui_languages"],
                currency_default=ruleset_data["currency_default"],
                special_rules=ruleset_data.get("special_rules"),
                supported_document_types=ruleset_data.get("supported_document_types", ["INVOICE"]),
            )
            session.add(ruleset)
            logger.info(f"Ruleset {ruleset_id} v{version} erstellt")

        count += 1

    await session.commit()
    return count
