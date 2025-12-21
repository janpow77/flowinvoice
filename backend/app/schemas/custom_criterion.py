"""
Schemas für Custom Criteria.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CustomCriterionCreate(BaseModel):
    """Schema für das Erstellen eines Custom Criterion."""

    name: str = Field(..., min_length=1, max_length=255, description="Name der Regel")
    description: Optional[str] = Field(None, description="Beschreibung der Regel")
    error_code: str = Field(..., min_length=1, max_length=50, description="Fehlercode (z.B. CUSTOM_001)")
    severity: str = Field("MEDIUM", description="Schweregrad (LOW, MEDIUM, HIGH, CRITICAL)")
    logic_type: str = Field("SIMPLE_COMPARISON", description="Logik-Typ")
    rule_config: dict[str, Any] = Field(default_factory=dict, description="Regelkonfiguration")
    error_message_template: str = Field(
        "Kriterium '{name}' nicht erfüllt.",
        description="Fehlermeldungsvorlage mit Platzhaltern",
    )
    priority: int = Field(0, ge=-100, le=100, description="Priorität")
    project_id: Optional[str] = Field(None, description="Projekt-ID (optional)")
    ruleset_id: Optional[str] = Field(None, description="Regelwerk-ID (optional)")


class CustomCriterionUpdate(BaseModel):
    """Schema für das Aktualisieren eines Custom Criterion."""

    name: Optional[str] = None
    description: Optional[str] = None
    error_code: Optional[str] = None
    severity: Optional[str] = None
    logic_type: Optional[str] = None
    rule_config: Optional[dict[str, Any]] = None
    error_message_template: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class CustomCriterionResponse(BaseModel):
    """Schema für die Antwort eines Custom Criterion."""

    id: str
    project_id: Optional[str]
    ruleset_id: Optional[str]
    name: str
    description: Optional[str]
    error_code: str
    severity: str
    is_active: bool
    logic_type: str
    rule_config: dict[str, Any]
    error_message_template: str
    priority: int
    created_by_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomCriterionListResponse(BaseModel):
    """Response für Custom Criteria Liste."""

    criteria: list[CustomCriterionResponse]
    total: int


class CriterionEvaluationResult(BaseModel):
    """Ergebnis einer Kriterien-Evaluierung."""

    criterion_id: str
    criterion_name: str
    error_code: str
    passed: bool
    severity: str
    message: str
    field: Optional[str] = None
    expected: Any = None
    actual: Any = None


class EvaluateRequest(BaseModel):
    """Request für Kriterien-Evaluierung."""

    document_data: dict[str, Any] = Field(..., description="Dokumentdaten zur Prüfung")
    criterion_ids: Optional[list[str]] = Field(None, description="Spezifische Kriterien (optional)")


class EvaluateResponse(BaseModel):
    """Response für Kriterien-Evaluierung."""

    passed: bool
    total_checked: int
    passed_count: int
    failed_count: int
    results: list[CriterionEvaluationResult]


# Vordefinierte Rule-Config-Beispiele für die Dokumentation

RULE_CONFIG_EXAMPLES = {
    "SIMPLE_COMPARISON": {
        "example": {
            "field": "gross_amount",
            "operator": "<=",
            "value": 10000,
            "value_type": "number",
        },
        "description": "Vergleicht einen Feldwert mit einem festen Wert",
    },
    "FIELD_REQUIRED": {
        "example": {
            "field": "invoice_number",
            "condition": "not_empty",
        },
        "description": "Prüft ob ein Pflichtfeld vorhanden ist",
    },
    "DATE_RANGE": {
        "example": {
            "field": "invoice_date",
            "min_date": "project_start",
            "max_date": "project_end",
            "include_boundaries": True,
        },
        "description": "Prüft ob ein Datum in einem Bereich liegt",
    },
    "PATTERN_MATCH": {
        "example": {
            "field": "supplier_vat_id",
            "pattern": "^DE[0-9]{9}$",
            "case_sensitive": False,
        },
        "description": "Prüft ob ein Wert einem Regex-Pattern entspricht",
    },
    "LOOKUP": {
        "example": {
            "field": "supplier_name",
            "lookup_source": "blacklist",
            "lookup_values": ["Blocked GmbH", "Suspicious Inc"],
        },
        "description": "Prüft ob ein Wert in einer Black-/Whitelist ist",
    },
    "CONDITIONAL": {
        "example": {
            "if": {
                "field": "gross_amount",
                "operator": ">",
                "value": 5000,
            },
            "then": {
                "field": "supplier_vat_id",
                "condition": "not_empty",
            },
        },
        "description": "Bedingte Prüfung (wenn X, dann muss Y)",
    },
}
