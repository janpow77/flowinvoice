# Pfad: /backend/app/services/solution_parser.py
"""
Solution File Parser

Parst Lösungsdateien in verschiedenen Formaten (JSON, JSONL, CSV).
Verwendet für LLM-Training-Workflow mit bekannten Korrekturen.
"""

import csv
import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any

from app.models.enums import ErrorCategory, ErrorCode, Severity, SolutionFileFormat

logger = logging.getLogger(__name__)


@dataclass
class SolutionError:
    """Ein einzelner Fehler in einer Lösung."""

    code: str  # ErrorCode als String
    feature_id: str
    severity: str  # Severity als String
    expected: Any = None
    actual: Any = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "code": self.code,
            "feature_id": self.feature_id,
            "severity": self.severity,
            "expected": self.expected,
            "actual": self.actual,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SolutionError":
        """Erstellt aus Dictionary."""
        return cls(
            code=data.get("code", ""),
            feature_id=data.get("feature_id", ""),
            severity=data.get("severity", "MEDIUM"),
            expected=data.get("expected"),
            actual=data.get("actual"),
            message=data.get("message", ""),
        )


@dataclass
class SolutionEntry:
    """Ein Eintrag in der Lösungsdatei (eine Rechnung)."""

    position: int  # Position in der Liste (1-basiert)
    filename: str
    is_valid: bool
    errors: list[SolutionError] = field(default_factory=list)
    fields: dict[str, Any] = field(default_factory=dict)

    # Optionale Metadaten
    template: str | None = None
    generator_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "position": self.position,
            "filename": self.filename,
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "fields": self.fields,
            "template": self.template,
            "generator_version": self.generator_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], position: int | None = None) -> "SolutionEntry":
        """Erstellt aus Dictionary."""
        errors = [
            SolutionError.from_dict(e) if isinstance(e, dict) else e
            for e in data.get("errors", [])
        ]

        return cls(
            position=position if position is not None else data.get("position", 0),
            filename=data.get("filename", ""),
            is_valid=data.get("is_valid", True),
            errors=errors,
            fields=data.get("fields", {}),
            template=data.get("template"),
            generator_version=data.get("generator_version"),
        )

    @property
    def error_codes(self) -> list[str]:
        """Liste der Fehler-Codes."""
        return [e.code for e in self.errors]

    @property
    def has_errors(self) -> bool:
        """Hat Fehler."""
        return len(self.errors) > 0 or not self.is_valid


@dataclass
class ParsedSolutionFile:
    """Geparste Lösungsdatei."""

    format: SolutionFileFormat
    entries: list[SolutionEntry]
    generator_version: str | None = None
    generated_at: datetime | None = None
    source_file: str | None = None

    # Statistiken
    @property
    def total_count(self) -> int:
        """Gesamtanzahl Einträge."""
        return len(self.entries)

    @property
    def valid_count(self) -> int:
        """Anzahl gültiger Einträge."""
        return sum(1 for e in self.entries if e.is_valid)

    @property
    def invalid_count(self) -> int:
        """Anzahl ungültiger Einträge."""
        return sum(1 for e in self.entries if not e.is_valid)

    @property
    def error_count(self) -> int:
        """Gesamtanzahl Fehler."""
        return sum(len(e.errors) for e in self.entries)

    def get_entry_by_filename(self, filename: str) -> SolutionEntry | None:
        """Findet Eintrag nach Dateiname."""
        for entry in self.entries:
            if entry.filename == filename:
                return entry
        return None

    def get_entry_by_position(self, position: int) -> SolutionEntry | None:
        """Findet Eintrag nach Position."""
        for entry in self.entries:
            if entry.position == position:
                return entry
        return None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "format": self.format.value,
            "entries": [e.to_dict() for e in self.entries],
            "generator_version": self.generator_version,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "source_file": self.source_file,
            "statistics": {
                "total": self.total_count,
                "valid": self.valid_count,
                "invalid": self.invalid_count,
                "errors": self.error_count,
            },
        }


class SolutionFileParser:
    """
    Parser für Lösungsdateien.

    Unterstützt:
    - JSON: Einzelnes Objekt mit "invoices" Array
    - JSONL: Eine JSON-Zeile pro Rechnung
    - CSV: Spaltenbasiertes Format
    """

    # CSV-Feldnamen-Mapping
    CSV_FIELD_MAPPING = {
        "position": "position",
        "pos": "position",
        "filename": "filename",
        "file": "filename",
        "dateiname": "filename",
        "is_valid": "is_valid",
        "valid": "is_valid",
        "gueltig": "is_valid",
        "errors": "errors",
        "fehler": "errors",
        "error_codes": "errors",
        "invoice_number": "invoice_number",
        "rechnungsnummer": "invoice_number",
        "invoice_date": "invoice_date",
        "rechnungsdatum": "invoice_date",
        "net_amount": "net_amount",
        "netto": "net_amount",
        "nettobetrag": "net_amount",
        "vat_rate": "vat_rate",
        "mwst_satz": "vat_rate",
        "steuersatz": "vat_rate",
        "vat_amount": "vat_amount",
        "mwst_betrag": "vat_amount",
        "gross_amount": "gross_amount",
        "brutto": "gross_amount",
        "bruttobetrag": "gross_amount",
        "supplier_name": "supplier_name",
        "lieferant": "supplier_name",
        "supplier_vat_id": "supplier_vat_id",
        "lieferant_ustid": "supplier_vat_id",
        "customer_name": "customer_name",
        "empfaenger": "customer_name",
        "kunde": "customer_name",
    }

    def __init__(self) -> None:
        """Initialisiert den Parser."""
        self.version = "1.0.0"

    def detect_format(self, content: str, filename: str | None = None) -> SolutionFileFormat:
        """
        Erkennt das Format der Lösungsdatei.

        Args:
            content: Dateiinhalt als String
            filename: Optionaler Dateiname für Erweiterungserkennung

        Returns:
            Erkanntes Format
        """
        # Erweiterung prüfen
        if filename:
            ext = Path(filename).suffix.lower()
            if ext == ".csv":
                return SolutionFileFormat.CSV
            if ext == ".jsonl":
                return SolutionFileFormat.JSONL

        # Content-Analyse
        content_stripped = content.strip()

        # JSON: Beginnt mit { oder [
        if content_stripped.startswith("{") or content_stripped.startswith("["):
            # Prüfen ob JSONL (mehrere Zeilen mit JSON-Objekten)
            lines = content_stripped.split("\n")
            if len(lines) > 1:
                try:
                    # Wenn jede Zeile valides JSON ist -> JSONL
                    for line in lines[:5]:  # Erste 5 Zeilen prüfen
                        if line.strip():
                            json.loads(line.strip())
                    return SolutionFileFormat.JSONL
                except json.JSONDecodeError:
                    pass
            return SolutionFileFormat.JSON

        # CSV: Prüfen auf typische CSV-Struktur
        if "," in content_stripped or ";" in content_stripped:
            return SolutionFileFormat.CSV

        # Fallback: JSON
        return SolutionFileFormat.JSON

    def parse(
        self,
        content: str,
        filename: str | None = None,
        format_hint: SolutionFileFormat | None = None,
    ) -> ParsedSolutionFile:
        """
        Parst eine Lösungsdatei.

        Args:
            content: Dateiinhalt als String
            filename: Optionaler Dateiname
            format_hint: Optionaler Format-Hinweis

        Returns:
            Geparste Lösungsdatei
        """
        # Format erkennen
        file_format = format_hint or self.detect_format(content, filename)

        # Je nach Format parsen
        if file_format == SolutionFileFormat.JSON:
            return self._parse_json(content, filename)
        elif file_format == SolutionFileFormat.JSONL:
            return self._parse_jsonl(content, filename)
        elif file_format == SolutionFileFormat.CSV:
            return self._parse_csv(content, filename)
        else:
            raise ValueError(f"Unbekanntes Format: {file_format}")

    def parse_file(self, file_path: str | Path) -> ParsedSolutionFile:
        """
        Parst eine Lösungsdatei von Disk.

        Args:
            file_path: Pfad zur Datei

        Returns:
            Geparste Lösungsdatei
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")

        with open(path, encoding="utf-8") as f:
            content = f.read()

        result = self.parse(content, path.name)
        result.source_file = str(path)
        return result

    def _parse_json(self, content: str, filename: str | None = None) -> ParsedSolutionFile:
        """Parst JSON-Format."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Ungültiges JSON: {e}") from e

        # Metadaten extrahieren
        generator_version = data.get("generator_version")
        generated_at = None
        if "generated_at" in data:
            try:
                generated_at = datetime.fromisoformat(
                    data["generated_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        # Einträge parsen
        entries: list[SolutionEntry] = []
        invoices = data.get("invoices", data.get("entries", []))

        # Wenn data selbst eine Liste ist
        if isinstance(data, list):
            invoices = data

        for idx, item in enumerate(invoices, start=1):
            entry = SolutionEntry.from_dict(item, position=idx)
            if entry.generator_version is None:
                entry.generator_version = generator_version
            entries.append(entry)

        return ParsedSolutionFile(
            format=SolutionFileFormat.JSON,
            entries=entries,
            generator_version=generator_version,
            generated_at=generated_at,
            source_file=filename,
        )

    def _parse_jsonl(self, content: str, filename: str | None = None) -> ParsedSolutionFile:
        """Parst JSONL-Format (eine JSON-Zeile pro Rechnung)."""
        entries: list[SolutionEntry] = []
        generator_version = None

        for idx, line in enumerate(content.strip().split("\n"), start=1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Zeile {idx} übersprungen (ungültiges JSON): {e}")
                continue

            entry = SolutionEntry.from_dict(data, position=idx)
            if generator_version is None and entry.generator_version:
                generator_version = entry.generator_version
            entries.append(entry)

        return ParsedSolutionFile(
            format=SolutionFileFormat.JSONL,
            entries=entries,
            generator_version=generator_version,
            source_file=filename,
        )

    def _parse_csv(self, content: str, filename: str | None = None) -> ParsedSolutionFile:
        """Parst CSV-Format."""
        entries: list[SolutionEntry] = []

        # Delimiter erkennen
        delimiter = "," if content.count(",") >= content.count(";") else ";"

        reader = csv.DictReader(StringIO(content), delimiter=delimiter)

        for idx, row in enumerate(reader, start=1):
            # Feldnamen normalisieren
            normalized_row: dict[str, Any] = {}
            for key, value in row.items():
                if key is None:
                    continue
                normalized_key = self.CSV_FIELD_MAPPING.get(key.lower().strip(), key.lower().strip())
                normalized_row[normalized_key] = value

            # Entry erstellen
            fields: dict[str, Any] = {}
            errors: list[SolutionError] = []

            # Standard-Felder extrahieren
            position = int(normalized_row.get("position", idx))
            filename_val = normalized_row.get("filename", f"row_{idx}")

            # is_valid parsen
            is_valid_str = str(normalized_row.get("is_valid", "true")).lower()
            is_valid = is_valid_str in ("true", "1", "yes", "ja", "y", "j")

            # Fehler-Codes parsen (kommagetrennt)
            error_str = normalized_row.get("errors", "")
            if error_str:
                for code in error_str.split(","):
                    code = code.strip()
                    if code:
                        errors.append(SolutionError(
                            code=code,
                            feature_id=self._infer_feature_from_code(code),
                            severity="HIGH",
                        ))

            # Rechnungsfelder extrahieren
            field_keys = [
                "invoice_number", "invoice_date", "net_amount", "vat_rate",
                "vat_amount", "gross_amount", "supplier_name", "supplier_vat_id",
                "customer_name", "service_description", "supply_date",
            ]
            for key in field_keys:
                if key in normalized_row and normalized_row[key]:
                    value = normalized_row[key]
                    # Numerische Werte konvertieren
                    if key in ("net_amount", "vat_amount", "gross_amount", "vat_rate"):
                        try:
                            value = float(value.replace(",", "."))
                        except (ValueError, AttributeError):
                            pass
                    fields[key] = value

            entry = SolutionEntry(
                position=position,
                filename=filename_val,
                is_valid=is_valid,
                errors=errors,
                fields=fields,
            )
            entries.append(entry)

        return ParsedSolutionFile(
            format=SolutionFileFormat.CSV,
            entries=entries,
            source_file=filename,
        )

    def _infer_feature_from_code(self, code: str) -> str:
        """Leitet Feature-ID aus Fehler-Code ab."""
        # Feature-ID Mapping basierend auf Fehler-Code-Präfix
        code_to_feature = {
            "TAX_SUPPLIER_NAME": "supplier_name",
            "TAX_SUPPLIER_ADDRESS": "supplier_address",
            "TAX_CUSTOMER_NAME": "customer_name",
            "TAX_CUSTOMER_ADDRESS": "customer_address",
            "TAX_ID": "tax_id",
            "TAX_INVOICE_DATE": "invoice_date",
            "TAX_INVOICE_NUMBER": "invoice_number",
            "TAX_SERVICE_DESCRIPTION": "service_description",
            "TAX_SUPPLY_DATE": "supply_date_or_period",
            "TAX_NET_AMOUNT": "net_amount",
            "TAX_VAT_RATE": "vat_rate",
            "TAX_VAT_AMOUNT": "vat_amount",
            "TAX_GROSS_AMOUNT": "gross_amount",
            "PROJECT_PERIOD": "supply_in_project_period",
            "PROJECT_RECIPIENT": "recipient_is_beneficiary",
            "PROJECT_LOCATION": "service_location_match",
            "PROJECT_REFERENCE": "project_reference",
            "FRAUD_SELF_INVOICE": "self_invoice_check",
            "FRAUD_CIRCULAR": "circular_invoice_check",
            "FRAUD_DUPLICATE": "duplicate_check",
            "FRAUD_ROUND_AMOUNT": "round_amount_check",
            "FRAUD_VENDOR": "vendor_clustering",
            "SEMANTIC_PROJECT": "semantic_project_relevance",
            "SEMANTIC_RED_FLAG": "no_red_flags",
            "ECONOMIC_HIGH": "economic_plausibility",
            "ECONOMIC_ABOVE": "economic_plausibility",
            "ECONOMIC_STATISTICAL": "no_statistical_anomalies",
        }

        for prefix, feature in code_to_feature.items():
            if code.startswith(prefix):
                return feature

        return "unknown"


# Singleton-Instanz
solution_parser = SolutionFileParser()
