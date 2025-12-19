# Pfad: /backend/app/schemas/ruleset_sample.py
"""
FlowAudit Ruleset Sample Schemas

Schemas für Musterdokumente von Regelwerken.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SampleStatus


class RulesetSampleBase(BaseModel):
    """Basis-Schema für Ruleset-Samples."""

    model_config = ConfigDict(from_attributes=True)

    ruleset_id: str = Field(..., description="Ruleset-ID")
    ruleset_version: str = Field(default="1.0.0", description="Ruleset-Version")
    description: str | None = Field(default=None, description="Beschreibung des Samples")


class RulesetSampleCreate(RulesetSampleBase):
    """Schema für Sample-Upload (ohne Datei, die kommt als FormData)."""

    pass


class RulesetSampleUpdate(BaseModel):
    """Schema für Ground-Truth-Update."""

    model_config = ConfigDict(from_attributes=True)

    description: str | None = Field(default=None, description="Beschreibung")
    ground_truth: dict[str, Any] | None = Field(default=None, description="Korrigierte Ground Truth")


class ExtractedFeature(BaseModel):
    """Ein extrahiertes Feature."""

    model_config = ConfigDict(from_attributes=True)

    feature_id: str = Field(..., description="Feature-ID")
    value: Any = Field(..., description="Extrahierter Wert")
    confidence: float | None = Field(default=None, description="Konfidenz (0-1)")
    raw_text: str | None = Field(default=None, description="Roh-Text aus dem Dokument")


class RulesetSampleResponse(BaseModel):
    """Response-Schema für ein Sample."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Sample-ID")
    ruleset_id: str = Field(..., description="Ruleset-ID")
    ruleset_version: str = Field(..., description="Ruleset-Version")
    filename: str = Field(..., description="Dateiname")
    file_size: int = Field(..., description="Dateigröße in Bytes")
    mime_type: str = Field(..., description="MIME-Type")
    description: str | None = Field(default=None, description="Beschreibung")
    status: SampleStatus = Field(..., description="Sample-Status")

    # Extrahierte Daten
    extracted_data: dict[str, Any] | None = Field(default=None, description="Extrahierte Daten")
    ground_truth: dict[str, Any] | None = Field(default=None, description="Ground Truth (korrigiert)")
    parse_error: str | None = Field(default=None, description="Parse-Fehler falls vorhanden")

    # Zeitstempel
    created_at: datetime = Field(..., description="Erstellungszeitpunkt")
    updated_at: datetime = Field(..., description="Letztes Update")
    processed_at: datetime | None = Field(default=None, description="Verarbeitungszeitpunkt")
    approved_at: datetime | None = Field(default=None, description="Genehmigungszeitpunkt")


class RulesetSampleListItem(BaseModel):
    """Kurzform für Listen."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Sample-ID")
    filename: str = Field(..., description="Dateiname")
    description: str | None = Field(default=None, description="Beschreibung")
    status: SampleStatus = Field(..., description="Sample-Status")
    created_at: datetime = Field(..., description="Erstellungszeitpunkt")
    has_ground_truth: bool = Field(default=False, description="Ground Truth vorhanden")


class RulesetSampleListResponse(BaseModel):
    """Response für Sample-Liste."""

    model_config = ConfigDict(from_attributes=True)

    data: list[RulesetSampleListItem] = Field(..., description="Sample-Liste")
    total: int = Field(..., description="Gesamtanzahl")
    stats: dict[str, int] = Field(default_factory=dict, description="Status-Statistik")


class SampleApproveRequest(BaseModel):
    """Request für Sample-Approval."""

    model_config = ConfigDict(from_attributes=True)

    ground_truth: dict[str, Any] | None = Field(
        default=None, description="Finale Ground Truth (optional, falls bereits gesetzt)"
    )


class SampleRejectRequest(BaseModel):
    """Request für Sample-Rejection."""

    model_config = ConfigDict(from_attributes=True)

    reason: str | None = Field(default=None, description="Ablehnungsgrund")
