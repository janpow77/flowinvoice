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
