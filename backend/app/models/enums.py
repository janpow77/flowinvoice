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
    PRECHECKED = "PRECHECKED"
    PREPARED = "PREPARED"
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
