# Pfad: /backend/app/schemas/document.py
"""
FlowAudit Document Schemas

Schemas für Dokumente (Rechnungen) und Parse/Precheck-Runs.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentStatus


class DocumentUploadItem(BaseModel):
    """Einzelnes hochgeladenes Dokument."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Dokument-ID")
    filename: str = Field(..., description="Dateiname")
    sha256: str = Field(..., description="SHA-256 Hash")
    status: DocumentStatus = Field(..., description="Status")
    is_duplicate_in_project: bool = Field(
        default=False, description="Duplikat im Projekt"
    )


class DocumentUploadResponse(BaseModel):
    """Response für Dokument-Upload."""

    model_config = ConfigDict(from_attributes=True)

    data: list[DocumentUploadItem] = Field(..., description="Hochgeladene Dokumente")


class DocumentCreate(BaseModel):
    """Dokument erstellen (intern)."""

    model_config = ConfigDict(from_attributes=True)

    project_id: str = Field(..., description="Projekt-ID")
    filename: str = Field(..., description="Dateiname")
    original_filename: str = Field(..., description="Originalname")
    sha256: str = Field(..., description="SHA-256 Hash")
    file_size_bytes: int | None = Field(default=None, description="Dateigröße")
    storage_path: str = Field(..., description="Speicherpfad")
    ruleset_id: str | None = Field(default=None, description="Ruleset-ID")
    ruleset_version: str | None = Field(default=None, description="Ruleset-Version")
    ui_language: str = Field(default="de", description="UI-Sprache")


class DocumentResponse(BaseModel):
    """Dokument-Response."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., alias="id", description="Dokument-ID")
    project_id: str = Field(..., description="Projekt-ID")
    filename: str = Field(..., description="Dateiname")
    original_filename: str = Field(..., description="Originalname")
    sha256: str = Field(..., description="SHA-256 Hash")
    file_size_bytes: int | None = Field(default=None, description="Dateigröße")
    status: DocumentStatus = Field(..., description="Status")
    ruleset_id: str | None = Field(default=None, description="Ruleset-ID")
    ruleset_version: str | None = Field(default=None, description="Ruleset-Version")
    ui_language: str = Field(default="de", description="UI-Sprache")
    error_message: str | None = Field(default=None, description="Fehlermeldung")
    created_at: datetime = Field(..., description="Erstellt")
    updated_at: datetime | None = Field(default=None, description="Aktualisiert")


class DocumentListItem(BaseModel):
    """Dokument in Listenansicht."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Dokument-ID")
    filename: str = Field(..., description="Dateiname")
    status: DocumentStatus = Field(..., description="Status")
    ruleset_id: str | None = Field(default=None, description="Ruleset")
    created_at: datetime = Field(..., description="Erstellt")


class ParseToken(BaseModel):
    """Parser-Token mit Position."""

    model_config = ConfigDict(from_attributes=True)

    text: str = Field(..., description="Token-Text")
    bbox: dict[str, Any] | None = Field(default=None, description="Bounding Box")


class ParsePage(BaseModel):
    """Geparste Seite."""

    model_config = ConfigDict(from_attributes=True)

    page: int = Field(..., description="Seitennummer")
    tokens: list[ParseToken] = Field(default_factory=list, description="Tokens")
    text: str | None = Field(default=None, description="Volltext")


class ExtractedValue(BaseModel):
    """Extrahierter Wert mit Konfidenz."""

    model_config = ConfigDict(from_attributes=True)

    value: Any = Field(..., description="Extrahierter Wert")
    confidence: float = Field(default=0.0, description="Konfidenz (0-1)")
    source: str = Field(default="regex", description="Extraktionsquelle")


class ParseRunCreate(BaseModel):
    """Parse-Run erstellen."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Dokument-ID")
    engine: str = Field(default="HYBRID", description="Parse-Engine")


class ParseRunResponse(BaseModel):
    """Parse-Run Response."""

    model_config = ConfigDict(from_attributes=True)

    parse_run_id: str = Field(..., alias="id", description="Parse-Run-ID")
    document_id: str = Field(..., description="Dokument-ID")
    engine: str = Field(..., description="Parse-Engine")
    status: str = Field(..., description="Status")
    timings_ms: dict[str, int] | None = Field(default=None, description="Timing")
    outputs: dict[str, Any] | None = Field(default=None, description="Outputs")
    error_message: str | None = Field(default=None, description="Fehlermeldung")
    created_at: datetime = Field(..., description="Erstellt")
    completed_at: datetime | None = Field(default=None, description="Abgeschlossen")


class ParsedDocumentResponse(BaseModel):
    """Vollständiges Parse-Ergebnis."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Dokument-ID")
    engine: str = Field(..., description="Parse-Engine")
    raw_text: str | None = Field(default=None, description="Volltext")
    pages: list[ParsePage] = Field(default_factory=list, description="Seiten")
    extracted: dict[str, ExtractedValue] | None = Field(
        default=None, description="Extrahierte Werte"
    )


class PrecheckItem(BaseModel):
    """Einzelne Precheck-Prüfung."""

    model_config = ConfigDict(from_attributes=True)

    check_id: str = Field(..., description="Check-ID")
    status: str = Field(..., description="OK | WARN | FAIL | UNKNOWN")
    observed: dict[str, Any] | None = Field(
        default=None, description="Beobachtete Werte"
    )
    comment: str | None = Field(default=None, description="Kommentar")
    confidence: float = Field(default=1.0, description="Konfidenz")


class PrecheckRunCreate(BaseModel):
    """Precheck-Run erstellen."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Dokument-ID")


class PrecheckRunResponse(BaseModel):
    """Precheck-Run Response."""

    model_config = ConfigDict(from_attributes=True)

    precheck_run_id: str = Field(..., alias="id", description="Precheck-Run-ID")
    document_id: str = Field(..., description="Dokument-ID")
    status: str = Field(..., description="Status")
    checks: list[PrecheckItem] = Field(default_factory=list, description="Checks")
    error_message: str | None = Field(default=None, description="Fehlermeldung")
    created_at: datetime = Field(..., description="Erstellt")
    completed_at: datetime | None = Field(default=None, description="Abgeschlossen")


class DocumentDeleteResponse(BaseModel):
    """Response für Dokument-Löschung."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Gelöschte Dokument-ID")
    filename: str = Field(..., description="Dateiname")
    deleted: bool = Field(..., description="Erfolgreich gelöscht")
    file_deleted: bool = Field(..., description="Datei vom Speicher entfernt")
    message: str = Field(..., description="Status-Nachricht")
