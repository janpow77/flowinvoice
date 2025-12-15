# Pfad: /backend/app/services/parser.py
"""
FlowAudit PDF Parser

Extrahiert Text und strukturierte Daten aus PDF-Rechnungen.
Verwendet pdfplumber für OCR-freies Parsing.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Bounding Box für PDF-Position (normalisiert 0-1)."""

    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float = 1.0


@dataclass
class ExtractedToken:
    """Extrahierter Token mit Position."""

    text: str
    bbox: BoundingBox | None = None


@dataclass
class ExtractedValue:
    """Extrahierter Wert mit Metadaten."""

    value: Any
    raw_text: str
    confidence: float = 0.0
    source: str = "regex"
    bbox: BoundingBox | None = None


@dataclass
class ParsedPage:
    """Geparste Seite."""

    page_number: int
    width: float
    height: float
    text: str
    tokens: list[ExtractedToken] = field(default_factory=list)


@dataclass
class ParseResult:
    """Ergebnis des PDF-Parsings."""

    raw_text: str
    pages: list[ParsedPage]
    extracted: dict[str, ExtractedValue]
    timings_ms: dict[str, int]
    error: str | None = None


class PDFParser:
    """
    PDF-Parser für Rechnungen.

    Extrahiert:
    - Volltext
    - Tokens mit Positionen
    - Strukturierte Daten (Datum, Beträge, IDs)
    """

    # Regex-Patterns für deutsche Rechnungen
    PATTERNS = {
        # Rechnungsnummer
        "invoice_number": [
            r"(?:Rechnungs?(?:nummer|nr\.?|#)|Invoice\s*(?:No\.?|Number|#))[:\s]*([A-Za-z0-9\-\/\.]+)",
            r"(?:Rechnung|Invoice)[:\s]*(?:Nr\.?|No\.?)[:\s]*([A-Za-z0-9\-\/\.]+)",
            r"(?:Nr\.|No\.)[:\s]*([A-Za-z0-9\-\/]+)",
        ],
        # Rechnungsdatum
        "invoice_date": [
            r"(?:Rechnungsdatum|Datum|Date|Invoice\s*Date)[:\s]*(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})",
            r"(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{4})",
        ],
        # Leistungszeitraum
        "supply_date_or_period": [
            r"(?:Leistungs(?:zeitraum|datum)|Lieferdatum|Zeitraum|Period)[:\s]*(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4}(?:\s*[-–bis]\s*\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})?)",
            r"(?:vom|from)[:\s]*(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{4})\s*(?:bis|to|-|–)\s*(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{4})",
        ],
        # Steuernummer
        "tax_number": [
            r"(?:Steuer(?:nummer|nr\.?)|Tax\s*(?:No\.?|Number))[:\s]*(\d{2,3}[\/\s]?\d{3,4}[\/\s]?\d{4,5})",
            r"St\.?-?Nr\.?[:\s]*(\d{2,3}[\/\s]?\d{3,4}[\/\s]?\d{4,5})",
        ],
        # USt-IdNr
        "vat_id": [
            r"(?:USt\.?-?(?:Id\.?-?)?Nr\.?|VAT\s*(?:ID|No\.?)|UID)[:\s]*([A-Z]{2}\s?\d{8,12})",
            r"(DE\s?\d{9})",
            r"(AT\s?U\d{8})",
        ],
        # Nettobetrag
        "net_amount": [
            r"(?:Netto(?:betrag)?|Zwischensumme|Subtotal|Net)[:\s]*€?\s*(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})\s*€?",
            r"(?:Summe\s+netto|Nettosumme)[:\s]*€?\s*(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})\s*€?",
        ],
        # MwSt-Betrag
        "vat_amount": [
            r"(?:MwSt\.?|USt\.?|VAT|Mehrwertsteuer|Umsatzsteuer)[:\s]*(?:\d{1,2}\s*%)?[:\s]*€?\s*(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})\s*€?",
            r"(?:zzgl\.?\s*)?(?:\d{1,2}\s*%\s*)?(?:MwSt\.?|USt\.?)[:\s]*€?\s*(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})\s*€?",
        ],
        # Bruttobetrag
        "gross_amount": [
            r"(?:Brutto(?:betrag)?|Gesamt(?:betrag)?|Total|Rechnungsbetrag|Endbetrag)[:\s]*€?\s*(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})\s*€?",
            r"(?:Zu\s*zahlen|Zahlbetrag)[:\s]*€?\s*(\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2})\s*€?",
        ],
        # MwSt-Satz
        "vat_rate": [
            r"(\d{1,2})\s*%\s*(?:MwSt\.?|USt\.?|VAT)",
            r"(?:MwSt\.?|USt\.?|VAT)[:\s]*(\d{1,2})\s*%",
        ],
        # IBAN
        "iban": [
            r"(?:IBAN)[:\s]*([A-Z]{2}\d{2}[\s]?(?:[A-Z0-9]{4}[\s]?){3,7}[A-Z0-9]{0,2})",
            r"([A-Z]{2}\d{2}\s?(?:\d{4}\s?){4}\d{2})",
            r"(DE\d{2}\s?(?:\d{4}\s?){4}\d{2})",
        ],
        # BIC
        "bic": [
            r"(?:BIC|SWIFT)[:\s]*([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)",
        ],
    }

    # Datumsformate
    DATE_FORMATS = [
        "%d.%m.%Y",
        "%d.%m.%y",
        "%d/%m/%Y",
        "%d/%m/%y",
        "%Y-%m-%d",
        "%d-%m-%Y",
    ]

    def __init__(self, timeout_sec: int = 30, max_pages: int = 50):
        """
        Initialisiert den Parser.

        Args:
            timeout_sec: Timeout für Parsing
            max_pages: Maximale Seitenanzahl
        """
        self.timeout_sec = timeout_sec
        self.max_pages = max_pages

    def parse(self, file_path: str | Path) -> ParseResult:
        """
        Parst eine PDF-Datei.

        Args:
            file_path: Pfad zur PDF-Datei

        Returns:
            ParseResult mit extrahierten Daten
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return ParseResult(
                raw_text="",
                pages=[],
                extracted={},
                timings_ms={},
                error=f"File not found: {file_path}",
            )

        start_time = time.time()
        timings: dict[str, int] = {}

        try:
            # PDF öffnen
            pdf_start = time.time()
            with pdfplumber.open(file_path) as pdf:
                timings["pdf_open"] = int((time.time() - pdf_start) * 1000)

                pages: list[ParsedPage] = []
                all_text_parts: list[str] = []

                # Seiten verarbeiten
                extract_start = time.time()
                for i, page in enumerate(pdf.pages[: self.max_pages]):
                    parsed_page = self._parse_page(page, i + 1)
                    pages.append(parsed_page)
                    all_text_parts.append(parsed_page.text)

                timings["text_extraction"] = int((time.time() - extract_start) * 1000)

                raw_text = "\n\n".join(all_text_parts)

                # Strukturierte Extraktion
                regex_start = time.time()
                extracted = self._extract_structured_data(raw_text, pages)
                timings["regex_extraction"] = int((time.time() - regex_start) * 1000)

                timings["total"] = int((time.time() - start_time) * 1000)

                return ParseResult(
                    raw_text=raw_text,
                    pages=pages,
                    extracted=extracted,
                    timings_ms=timings,
                )

        except Exception as e:
            logger.exception(f"Error parsing PDF: {e}")
            return ParseResult(
                raw_text="",
                pages=[],
                extracted={},
                timings_ms={"total": int((time.time() - start_time) * 1000)},
                error=str(e),
            )

    def _parse_page(self, page: Any, page_number: int) -> ParsedPage:
        """
        Parst eine einzelne Seite.

        Args:
            page: pdfplumber Page-Objekt
            page_number: Seitennummer (1-basiert)

        Returns:
            ParsedPage
        """
        width = page.width
        height = page.height

        # Text extrahieren
        text = page.extract_text() or ""

        # Tokens mit Positionen
        tokens: list[ExtractedToken] = []
        words = page.extract_words() or []

        for word in words:
            bbox = BoundingBox(
                page=page_number,
                x0=word["x0"] / width,
                y0=word["top"] / height,
                x1=word["x1"] / width,
                y1=word["bottom"] / height,
                confidence=0.95,  # pdfplumber hat keine Konfidenz, wir setzen hohen Default
            )
            tokens.append(ExtractedToken(text=word["text"], bbox=bbox))

        return ParsedPage(
            page_number=page_number,
            width=width,
            height=height,
            text=text,
            tokens=tokens,
        )

    def _extract_structured_data(
        self, text: str, pages: list[ParsedPage]
    ) -> dict[str, ExtractedValue]:
        """
        Extrahiert strukturierte Daten mittels Regex.

        Args:
            text: Volltext
            pages: Geparste Seiten

        Returns:
            Dict mit extrahierten Werten
        """
        extracted: dict[str, ExtractedValue] = {}

        for field_name, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    raw_value = match.group(1) if match.groups() else match.group(0)

                    # Wert konvertieren
                    converted_value = self._convert_value(field_name, raw_value)

                    # BoundingBox finden (erste Seite mit Match)
                    bbox = self._find_bbox(raw_value, pages)

                    extracted[field_name] = ExtractedValue(
                        value=converted_value,
                        raw_text=raw_value,
                        confidence=0.8 if bbox else 0.6,
                        source="regex",
                        bbox=bbox,
                    )
                    break

        return extracted

    def _convert_value(self, field_name: str, raw_value: str) -> Any:
        """
        Konvertiert Rohwert in typisierten Wert.

        Args:
            field_name: Feldname
            raw_value: Rohwert

        Returns:
            Konvertierter Wert
        """
        # Datums-Felder
        if "date" in field_name:
            return self._parse_date(raw_value)

        # Betrags-Felder
        if "amount" in field_name:
            return self._parse_amount(raw_value)

        # Prozent-Felder
        if "rate" in field_name:
            try:
                return int(re.sub(r"[^\d]", "", raw_value))
            except ValueError:
                return raw_value

        # Standard: String bereinigen
        return raw_value.strip()

    def _parse_date(self, value: str) -> date | str:
        """
        Parst Datum aus verschiedenen Formaten.

        Args:
            value: Datums-String

        Returns:
            date-Objekt oder Original-String
        """
        clean_value = value.strip()

        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(clean_value, fmt).date()
            except ValueError:
                continue

        return clean_value

    def _parse_amount(self, value: str) -> Decimal | str:
        """
        Parst Geldbetrag.

        Args:
            value: Betrags-String

        Returns:
            Decimal oder Original-String
        """
        # Entferne Währungssymbole und Whitespace
        clean_value = re.sub(r"[€$£\s]", "", value)

        # Deutsche Notation: 1.234,56 -> 1234.56
        if "," in clean_value and "." in clean_value:
            # Tausendertrennzeichen entfernen
            if clean_value.rfind(",") > clean_value.rfind("."):
                # Deutsches Format: 1.234,56
                clean_value = clean_value.replace(".", "").replace(",", ".")
            else:
                # Englisches Format: 1,234.56
                clean_value = clean_value.replace(",", "")
        elif "," in clean_value:
            # Nur Komma -> Dezimaltrennzeichen
            clean_value = clean_value.replace(",", ".")

        try:
            return Decimal(clean_value)
        except InvalidOperation:
            return value

    def _find_bbox(
        self, text: str, pages: list[ParsedPage]
    ) -> BoundingBox | None:
        """
        Findet BoundingBox für Text.

        Args:
            text: Zu suchender Text
            pages: Geparste Seiten

        Returns:
            BoundingBox oder None
        """
        search_text = text.lower().strip()

        for page in pages:
            for token in page.tokens:
                if search_text in token.text.lower():
                    return token.bbox

        return None


# Singleton-Instanz
_parser: PDFParser | None = None


def get_parser() -> PDFParser:
    """
    Gibt Parser-Singleton zurück.

    Returns:
        PDFParser-Instanz
    """
    global _parser
    if _parser is None:
        _parser = PDFParser()
    return _parser
