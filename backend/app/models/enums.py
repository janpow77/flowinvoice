# Pfad: /backend/app/models/enums.py
"""
FlowAudit Enumerations

Alle Enums für das System, entsprechend api_contracts.md.
"""

from enum import Enum


class Role(str, Enum):
    """Benutzerrollen."""

    USER = "user"
    ADMIN = "admin"


class RulesetId(str, Enum):
    """Unterstützte Regelwerke."""

    DE_USTG = "DE_USTG"
    EU_VAT = "EU_VAT"
    UK_VAT = "UK_VAT"


class UiLanguage(str, Enum):
    """UI-Sprachen."""

    DE = "de"
    EN = "en"


class DocumentType(str, Enum):
    """Dokumenttyp für die Kategorisierung."""

    INVOICE = "INVOICE"  # Rechnung
    BANK_STATEMENT = "BANK_STATEMENT"  # Kontoauszug
    PROCUREMENT = "PROCUREMENT"  # Vergabeunterlagen
    CONTRACT = "CONTRACT"  # Vertrag
    OTHER = "OTHER"  # Sonstiges


class DocumentStatus(str, Enum):
    """Dokumentstatus im Verarbeitungsablauf."""

    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    PARSED = "PARSED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    PRECHECKED = "PRECHECKED"
    PREPARED = "PREPARED"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    LLM_RUNNING = "LLM_RUNNING"
    LLM_DONE = "LLM_DONE"
    REVIEW_PENDING = "REVIEW_PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPORTED = "EXPORTED"
    ERROR = "ERROR"


class CheckStatus(str, Enum):
    """Merkmalstatus (Feature-Erkennung)."""

    PRESENT = "PRESENT"
    MISSING = "MISSING"
    UNCLEAR = "UNCLEAR"


class RuleCheckStatus(str, Enum):
    """Status einer Regelprüfung."""

    OK = "OK"
    WARN = "WARN"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class TruthSource(str, Enum):
    """Quelle des finalen Wertes."""

    RULE = "RULE"
    LLM = "LLM"
    USER = "USER"


class Provider(str, Enum):
    """LLM-Provider."""

    LOCAL_OLLAMA = "LOCAL_OLLAMA"
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    GEMINI = "GEMINI"


class FeedbackRating(str, Enum):
    """Feedback-Bewertung."""

    CORRECT = "CORRECT"
    PARTIAL = "PARTIAL"
    WRONG = "WRONG"


class RelationLevel(str, Enum):
    """Projektbezug-Grad."""

    YES = "YES"
    PARTIAL = "PARTIAL"
    UNCLEAR = "UNCLEAR"
    NO = "NO"


class LocationMatchStatus(str, Enum):
    """Standort-Übereinstimmungsstatus."""

    MATCH = "MATCH"
    PARTIAL = "PARTIAL"
    MISMATCH = "MISMATCH"
    UNCLEAR = "UNCLEAR"


class ErrorSourceCategory(str, Enum):
    """Fehlerquellen-Kategorie."""

    TAX_LAW = "TAX_LAW"
    BENEFICIARY_DATA = "BENEFICIARY_DATA"
    LOCATION_VALIDATION = "LOCATION_VALIDATION"


class TaxLawErrorType(str, Enum):
    """Detaillierte Fehlertypen für Steuerrecht."""

    MISSING = "MISSING"
    WRONG_FORMAT = "WRONG_FORMAT"
    CONFUSED_WITH_OTHER = "CONFUSED_WITH_OTHER"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    WRONG_RATE = "WRONG_RATE"
    NOT_UNIQUE = "NOT_UNIQUE"
    UNCLEAR = "UNCLEAR"
    OUT_OF_PROJECT_PERIOD = "OUT_OF_PROJECT_PERIOD"
    INVALID_CHECKSUM = "INVALID_CHECKSUM"
    COUNTRY_MISMATCH = "COUNTRY_MISMATCH"
    DATE_INVALID = "DATE_INVALID"


class JobStatus(str, Enum):
    """Generischer Job-Status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class ExportFormat(str, Enum):
    """Export-Formate."""

    XLSX = "XLSX"
    CSV = "CSV"
    JSON = "JSON"


class FeatureCategory(str, Enum):
    """Feature-Kategorien für Statistik."""

    IDENTITY = "IDENTITY"
    DATE = "DATE"
    AMOUNT = "AMOUNT"
    TAX = "TAX"
    TEXT = "TEXT"
    SEMANTIC = "SEMANTIC"
    PROJECT_CONTEXT = "PROJECT_CONTEXT"


class RequiredLevel(str, Enum):
    """Pflichtgrad eines Features."""

    REQUIRED = "REQUIRED"
    CONDITIONAL = "CONDITIONAL"
    OPTIONAL = "OPTIONAL"


class ExtractionType(str, Enum):
    """Extraktionstyp für Parser."""

    STRING = "STRING"
    TEXTBLOCK = "TEXTBLOCK"
    DATE = "DATE"
    DATE_RANGE = "DATE_RANGE"
    MONEY = "MONEY"
    PERCENTAGE = "PERCENTAGE"
    NUMBER = "NUMBER"


# ============================================================
# Improvement Catalog Enums (Phase 1)
# ============================================================


class ErrorSource(str, Enum):
    """Fehlerquelle für Nachvollziehbarkeit."""

    RULE = "RULE"  # Regelbasierte Prüfung
    LLM = "LLM"  # KI-Analyse
    USER = "USER"  # Manuelle Korrektur
    SYSTEM = "SYSTEM"  # Systemfehler


class Severity(str, Enum):
    """Schweregrad eines Fehlers."""

    INFO = "INFO"  # Hinweis, keine Aktion erforderlich
    LOW = "LOW"  # Geringer Schweregrad
    MEDIUM = "MEDIUM"  # Mittlerer Schweregrad
    HIGH = "HIGH"  # Hoher Schweregrad
    CRITICAL = "CRITICAL"  # Kritisch, blockiert Verarbeitung


class AnalysisStatus(str, Enum):
    """Analysestatus inkl. Fehler- und Abbruchzustände."""

    # Erfolgreiche Zustände
    COMPLETED = "COMPLETED"  # Analyse erfolgreich abgeschlossen
    REVIEW_NEEDED = "REVIEW_NEEDED"  # Manuelle Prüfung erforderlich

    # Fehlerzustände (fachlich relevant)
    DOCUMENT_UNREADABLE = "DOCUMENT_UNREADABLE"  # Dokument nicht lesbar
    INSUFFICIENT_TEXT = "INSUFFICIENT_TEXT"  # Zu wenig Text extrahiert
    RULESET_NOT_APPLICABLE = "RULESET_NOT_APPLICABLE"  # Ruleset nicht anwendbar
    ANALYSIS_ABORTED = "ANALYSIS_ABORTED"  # Analyse abgebrochen
    TIMEOUT = "TIMEOUT"  # Zeitüberschreitung

    # Systemfehler
    SYSTEM_ERROR = "SYSTEM_ERROR"  # Allgemeiner Systemfehler


class GrantPurposeDimension(str, Enum):
    """Prüfdimensionen für Zuwendungszweckprüfung."""

    SUBJECT_RELATION = "SUBJECT_RELATION"  # Sachlicher Zusammenhang
    TEMPORAL_RELATION = "TEMPORAL_RELATION"  # Zeitlicher Zusammenhang
    ORGANIZATIONAL_RELATION = "ORGANIZATIONAL_RELATION"  # Organisatorischer Zusammenhang
    ECONOMIC_PLAUSIBILITY = "ECONOMIC_PLAUSIBILITY"  # Wirtschaftliche Plausibilität


class DimensionResult(str, Enum):
    """Bewertungsergebnis pro Prüfdimension."""

    PASS = "PASS"  # Kriterium erfüllt
    FAIL = "FAIL"  # Kriterium nicht erfüllt
    UNCLEAR = "UNCLEAR"  # Nicht eindeutig bewertbar


class ConflictStatus(str, Enum):
    """Konfliktstatus zwischen verschiedenen Quellen."""

    NO_CONFLICT = "NO_CONFLICT"  # Übereinstimmung aller Quellen
    CONFLICT_RULE_LLM = "CONFLICT_RULE_LLM"  # Widerspruch zwischen Regel und KI
    CONFLICT_RULE_USER = "CONFLICT_RULE_USER"  # Manuelle Überschreibung von Regel
    CONFLICT_LLM_USER = "CONFLICT_LLM_USER"  # Manuelle Überschreibung von KI


class BeneficiaryMatchStatus(str, Enum):
    """Status des Begünstigtenabgleichs."""

    EXACT_MATCH = "EXACT_MATCH"  # Exakte Übereinstimmung
    ALIAS_MATCH = "ALIAS_MATCH"  # Übereinstimmung mit Alias
    LIKELY_MATCH = "LIKELY_MATCH"  # Wahrscheinliche Übereinstimmung (Fuzzy)
    MISMATCH = "MISMATCH"  # Keine Übereinstimmung
    NOT_CHECKED = "NOT_CHECKED"  # Nicht geprüft


class UnclearReason(str, Enum):
    """Gründe für UNCLEAR-Status (Begründungspflicht)."""

    MISSING_INFORMATION = "MISSING_INFORMATION"  # Relevante Informationen fehlen
    AMBIGUOUS_DATA = "AMBIGUOUS_DATA"  # Vorhandene Informationen mehrdeutig
    MULTIPLE_INTERPRETATIONS = "MULTIPLE_INTERPRETATIONS"  # Mehrere plausible Interpretationen
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"  # Kontext nicht ausreichend
    CONFLICTING_SOURCES = "CONFLICTING_SOURCES"  # Quellen widersprechen sich


class RiskIndicator(str, Enum):
    """Risikoindikatoren für didaktische Hinweise."""

    HIGH_AMOUNT = "HIGH_AMOUNT"  # Ungewöhnlich hoher Einzelbetrag
    VENDOR_CLUSTERING = "VENDOR_CLUSTERING"  # Auffällige Lieferantenhäufung
    MISSING_PERIOD = "MISSING_PERIOD"  # Fehlender Leistungszeitraum
    ROUND_AMOUNT = "ROUND_AMOUNT"  # Runder Pauschalbetrag ohne Erläuterung
    OUTSIDE_PROJECT_PERIOD = "OUTSIDE_PROJECT_PERIOD"  # Leistung außerhalb Projektzeitraum
    NO_PROJECT_REFERENCE = "NO_PROJECT_REFERENCE"  # Leistungsbeschreibung ohne Projektbezug
    RECIPIENT_MISMATCH = "RECIPIENT_MISMATCH"  # Rechnungsempfänger ≠ Begünstigter
    SELF_INVOICE = "SELF_INVOICE"  # Selbstrechnung: Lieferant-UST-ID = Begünstigter-UST-ID
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"  # Doppelte Rechnungsnummer


class DataClassification(str, Enum):
    """Datenklassifikation für Speicherung und Löschung."""

    INVOICE_DOCUMENT = "INVOICE_DOCUMENT"  # Rechnungsdokumente
    EXTRACTED_TEXT = "EXTRACTED_TEXT"  # Extrahierter Text
    ANALYSIS_RESULT = "ANALYSIS_RESULT"  # Analyseergebnisse (Audit-Trail)
    TRAINING_DATA = "TRAINING_DATA"  # Trainings-/Beispieldaten (RAG)


class SampleStatus(str, Enum):
    """Status eines Regelwerk-Musterdokuments."""

    UPLOADED = "UPLOADED"  # Hochgeladen, noch nicht verarbeitet
    PROCESSING = "PROCESSING"  # Wird geparst
    PENDING_REVIEW = "PENDING_REVIEW"  # Extraktion fertig, wartet auf Review
    APPROVED = "APPROVED"  # Ground Truth bestätigt, RAG-Beispiele erstellt
    REJECTED = "REJECTED"  # Sample abgelehnt (schlechte Qualität)


# ============================================================
# LLM Training Workflow Enums (Feature: feature_llm_training_workflow.md)
# ============================================================


class ErrorCategory(str, Enum):
    """Fehler-Kategorien für Training und Prüfung."""

    TAX = "TAX"  # Steuerrecht (§14 UStG)
    PROJECT = "PROJECT"  # Projektbezug
    FRAUD = "FRAUD"  # Betrugsindikatoren
    SEMANTIC = "SEMANTIC"  # KI-Prüfung
    ECONOMIC = "ECONOMIC"  # Wirtschaftlichkeit
    CUSTOM = "CUSTOM"  # Benutzerdefiniert


class ErrorCode(str, Enum):
    """
    Standardisierte Fehler-Codes für Generator und Prüfsystem.

    Format: {KATEGORIE}_{MERKMAL}_{TYP}
    """

    # ============ TAX (Steuerrecht §14 UStG) ============
    # Lieferant
    TAX_SUPPLIER_NAME_MISSING = "TAX_SUPPLIER_NAME_MISSING"
    TAX_SUPPLIER_NAME_INCOMPLETE = "TAX_SUPPLIER_NAME_INCOMPLETE"
    TAX_SUPPLIER_ADDRESS_MISSING = "TAX_SUPPLIER_ADDRESS_MISSING"
    TAX_SUPPLIER_ADDRESS_INCOMPLETE = "TAX_SUPPLIER_ADDRESS_INCOMPLETE"

    # Empfänger
    TAX_CUSTOMER_NAME_MISSING = "TAX_CUSTOMER_NAME_MISSING"
    TAX_CUSTOMER_ADDRESS_MISSING = "TAX_CUSTOMER_ADDRESS_MISSING"

    # Steuernummer
    TAX_ID_MISSING = "TAX_ID_MISSING"
    TAX_ID_INVALID_FORMAT = "TAX_ID_INVALID_FORMAT"

    # Rechnungsdaten
    TAX_INVOICE_DATE_MISSING = "TAX_INVOICE_DATE_MISSING"
    TAX_INVOICE_DATE_INVALID = "TAX_INVOICE_DATE_INVALID"
    TAX_INVOICE_DATE_FUTURE = "TAX_INVOICE_DATE_FUTURE"
    TAX_INVOICE_NUMBER_MISSING = "TAX_INVOICE_NUMBER_MISSING"
    TAX_INVOICE_NUMBER_DUPLICATE = "TAX_INVOICE_NUMBER_DUPLICATE"

    # Leistung
    TAX_SERVICE_DESCRIPTION_MISSING = "TAX_SERVICE_DESCRIPTION_MISSING"
    TAX_SERVICE_DESCRIPTION_VAGUE = "TAX_SERVICE_DESCRIPTION_VAGUE"
    TAX_SUPPLY_DATE_MISSING = "TAX_SUPPLY_DATE_MISSING"

    # Beträge
    TAX_NET_AMOUNT_MISSING = "TAX_NET_AMOUNT_MISSING"
    TAX_NET_AMOUNT_INVALID = "TAX_NET_AMOUNT_INVALID"
    TAX_VAT_RATE_MISSING = "TAX_VAT_RATE_MISSING"
    TAX_VAT_RATE_WRONG = "TAX_VAT_RATE_WRONG"
    TAX_VAT_RATE_INVALID = "TAX_VAT_RATE_INVALID"
    TAX_VAT_AMOUNT_MISSING = "TAX_VAT_AMOUNT_MISSING"
    TAX_VAT_AMOUNT_WRONG = "TAX_VAT_AMOUNT_WRONG"
    TAX_GROSS_AMOUNT_MISSING = "TAX_GROSS_AMOUNT_MISSING"
    TAX_GROSS_AMOUNT_WRONG = "TAX_GROSS_AMOUNT_WRONG"

    # ============ PROJECT (Projektbezug) ============
    PROJECT_PERIOD_BEFORE_START = "PROJECT_PERIOD_BEFORE_START"
    PROJECT_PERIOD_AFTER_END = "PROJECT_PERIOD_AFTER_END"
    PROJECT_PERIOD_OUTSIDE = "PROJECT_PERIOD_OUTSIDE"
    PROJECT_RECIPIENT_MISMATCH = "PROJECT_RECIPIENT_MISMATCH"
    PROJECT_LOCATION_MISMATCH = "PROJECT_LOCATION_MISMATCH"
    PROJECT_REFERENCE_MISSING = "PROJECT_REFERENCE_MISSING"
    PROJECT_REFERENCE_VAGUE = "PROJECT_REFERENCE_VAGUE"

    # ============ FRAUD (Betrugsindikatoren) ============
    FRAUD_SELF_INVOICE = "FRAUD_SELF_INVOICE"  # Lieferant-UST-ID = Empfänger-UST-ID
    FRAUD_CIRCULAR_INVOICE = "FRAUD_CIRCULAR_INVOICE"  # Zirkelrechnung
    FRAUD_DUPLICATE_INVOICE = "FRAUD_DUPLICATE_INVOICE"  # Bereits eingereicht
    FRAUD_ROUND_AMOUNT_PATTERN = "FRAUD_ROUND_AMOUNT_PATTERN"  # Verdächtige runde Beträge
    FRAUD_VENDOR_CLUSTERING = "FRAUD_VENDOR_CLUSTERING"  # Ungewöhnliche Lieferantenhäufung

    # ============ SEMANTIC (KI-Prüfung) ============
    SEMANTIC_NO_PROJECT_RELEVANCE = "SEMANTIC_NO_PROJECT_RELEVANCE"
    SEMANTIC_LOW_PROJECT_RELEVANCE = "SEMANTIC_LOW_PROJECT_RELEVANCE"
    SEMANTIC_RED_FLAG_LUXURY = "SEMANTIC_RED_FLAG_LUXURY"
    SEMANTIC_RED_FLAG_ENTERTAINMENT = "SEMANTIC_RED_FLAG_ENTERTAINMENT"
    SEMANTIC_RED_FLAG_PRIVATE = "SEMANTIC_RED_FLAG_PRIVATE"

    # ============ ECONOMIC (Wirtschaftlichkeit) ============
    ECONOMIC_HIGH_AMOUNT = "ECONOMIC_HIGH_AMOUNT"
    ECONOMIC_ABOVE_MARKET = "ECONOMIC_ABOVE_MARKET"
    ECONOMIC_STATISTICAL_OUTLIER = "ECONOMIC_STATISTICAL_OUTLIER"


class BatchJobStatus(str, Enum):
    """Status eines Batch-Jobs."""

    PENDING = "PENDING"  # Wartet auf Ausführung
    QUEUED = "QUEUED"  # In Celery-Queue eingereiht
    SCHEDULED = "SCHEDULED"  # Geplant (Celery Beat)
    RUNNING = "RUNNING"  # Läuft gerade
    PAUSED = "PAUSED"  # Pausiert
    COMPLETED = "COMPLETED"  # Erfolgreich abgeschlossen
    FAILED = "FAILED"  # Fehlgeschlagen
    CANCELLED = "CANCELLED"  # Abgebrochen


class SolutionFileFormat(str, Enum):
    """Unterstützte Lösungsdatei-Formate."""

    JSON = "JSON"
    JSONL = "JSONL"
    CSV = "CSV"


class MatchingStrategy(str, Enum):
    """Strategie für Lösungsdatei-Matching."""

    FILENAME = "FILENAME"  # Nur Dateiname
    FILENAME_POSITION = "FILENAME_POSITION"  # Dateiname + Position
    POSITION_ONLY = "POSITION_ONLY"  # Nur Position in Upload-Reihenfolge


class ChunkStrategy(str, Enum):
    """Chunking-Strategie für RAG."""

    FIXED = "fixed"  # Feste Token-Größe
    PARAGRAPH = "paragraph"  # An Absatzgrenzen
    SEMANTIC = "semantic"  # An Satzgrenzen


class CriterionLogicType(str, Enum):
    """Prüflogik-Typen für benutzerdefinierte Kriterien."""

    THRESHOLD = "threshold"  # Numerischer Vergleich
    REGEX = "regex"  # Musterprüfung
    BLACKLIST = "blacklist"  # Verbotene Werte
    WHITELIST = "whitelist"  # Erlaubte Werte
    DATE_RANGE = "date_range"  # Zeitraumprüfung
    COMPARISON = "comparison"  # Feldvergleich
    LLM_PROMPT = "llm_prompt"  # Semantische Prüfung via LLM


class FeatureStatus(str, Enum):
    """Status eines Features in der Dokumentenliste."""

    VALID = "VALID"  # Korrekt erkannt
    INVALID = "INVALID"  # Fehler erkannt
    WARNING = "WARNING"  # Warnung
    MISSING = "MISSING"  # Nicht gefunden
    PENDING = "PENDING"  # Noch nicht geprüft
    CORRECTED = "CORRECTED"  # Manuell korrigiert
