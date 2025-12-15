# Pfad: /backend/app/schemas/common.py
"""
FlowAudit Common Schemas

Gemeinsam genutzte Pydantic-Modelle.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Money(BaseModel):
    """Geldbetrag mit Währung."""

    model_config = ConfigDict(from_attributes=True)

    amount: str = Field(..., description="Betrag als String (z.B. '1234.56')")
    currency: str = Field(default="EUR", description="Währungscode (ISO 4217)")

    @classmethod
    def from_decimal(cls, amount: Decimal, currency: str = "EUR") -> "Money":
        """Erstellt Money aus Decimal."""
        return cls(amount=str(amount), currency=currency)


class DateRange(BaseModel):
    """Datumsbereich."""

    model_config = ConfigDict(from_attributes=True)

    start: date = Field(..., description="Startdatum")
    end: date = Field(..., description="Enddatum")


class BoundingBox(BaseModel):
    """Bounding Box für PDF-Positionen (normalisiert 0-1)."""

    model_config = ConfigDict(from_attributes=True)

    page: int = Field(..., ge=1, description="Seitennummer (1-basiert)")
    x0: float = Field(..., ge=0, le=1, description="Linke X-Koordinate (0-1)")
    y0: float = Field(..., ge=0, le=1, description="Obere Y-Koordinate (0-1)")
    x1: float = Field(..., ge=0, le=1, description="Rechte X-Koordinate (0-1)")
    y1: float = Field(..., ge=0, le=1, description="Untere Y-Koordinate (0-1)")
    confidence: float = Field(default=1.0, ge=0, le=1, description="Konfidenz (0-1)")


class Meta(BaseModel):
    """Response-Metadaten."""

    model_config = ConfigDict(from_attributes=True)

    request_id: str | None = Field(default=None, description="Request-ID")
    total: int | None = Field(default=None, description="Gesamtanzahl (bei Pagination)")
    limit: int | None = Field(default=None, description="Limit")
    offset: int | None = Field(default=None, description="Offset")


class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details."""

    model_config = ConfigDict(from_attributes=True)

    type: str = Field(..., description="Problem-Typ-URI")
    title: str = Field(..., description="Kurzbeschreibung")
    status: int = Field(..., description="HTTP-Statuscode")
    detail: str = Field(..., description="Detaillierte Beschreibung")
    instance: str | None = Field(default=None, description="Betroffene Ressourcen-URI")
    errors: list[dict[str, str]] | None = Field(
        default=None, description="Validierungsfehler"
    )
    timestamp: datetime | None = Field(default=None, description="Zeitstempel")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginierte Response."""

    model_config = ConfigDict(from_attributes=True)

    data: list[T] = Field(..., description="Ergebnisliste")
    meta: Meta = Field(..., description="Metadaten")


class BaseResponse(BaseModel):
    """Basis-Response mit optionalen Metadaten."""

    model_config = ConfigDict(from_attributes=True)

    data: Any | None = Field(default=None, description="Response-Daten")
    meta: Meta | None = Field(default=None, description="Metadaten")


class TimestampMixin(BaseModel):
    """Mixin für Zeitstempel."""

    created_at: datetime = Field(..., description="Erstellungszeitpunkt")
    updated_at: datetime | None = Field(default=None, description="Aktualisierungszeitpunkt")


class IdMixin(BaseModel):
    """Mixin für UUID-ID."""

    id: str = Field(..., description="UUID")
