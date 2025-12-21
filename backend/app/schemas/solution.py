# Pfad: /backend/app/schemas/solution.py
"""
FlowAudit Solution File Schemas

Schemas für Lösungsdatei-Import und -Verarbeitung.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MatchingStrategy, SolutionFileFormat


class SolutionErrorSchema(BaseModel):
    """Schema für einen einzelnen Fehler."""

    model_config = ConfigDict(from_attributes=True)

    code: str = Field(..., description="Fehler-Code (z.B. TAX_VAT_RATE_WRONG)")
    feature_id: str = Field(..., description="Betroffenes Feature")
    severity: str = Field(default="HIGH", description="Schweregrad")
    expected: Any = Field(default=None, description="Erwarteter Wert")
    actual: Any = Field(default=None, description="Tatsächlicher Wert")
    message: str = Field(default="", description="Fehlermeldung")


class SolutionEntrySchema(BaseModel):
    """Schema für einen Lösungsdatei-Eintrag."""

    model_config = ConfigDict(from_attributes=True)

    position: int = Field(..., ge=1, description="Position in der Liste (1-basiert)")
    filename: str = Field(..., description="Dateiname der Rechnung")
    is_valid: bool = Field(default=True, description="Rechnung ist fehlerfrei")
    errors: list[SolutionErrorSchema] = Field(
        default_factory=list, description="Liste der Fehler"
    )
    fields: dict[str, Any] = Field(
        default_factory=dict, description="Extrahierte Rechnungsfelder"
    )
    template: str | None = Field(default=None, description="Verwendetes Template")


class SolutionFileUploadResponse(BaseModel):
    """Response nach Upload einer Lösungsdatei."""

    model_config = ConfigDict(from_attributes=True)

    solution_file_id: str = Field(..., description="ID der gespeicherten Lösungsdatei")
    format: SolutionFileFormat = Field(..., description="Erkanntes Format")
    entry_count: int = Field(..., ge=0, description="Anzahl Einträge")
    valid_count: int = Field(..., ge=0, description="Anzahl gültiger Einträge")
    invalid_count: int = Field(..., ge=0, description="Anzahl ungültiger Einträge")
    error_count: int = Field(..., ge=0, description="Gesamtanzahl Fehler")
    generator_version: str | None = Field(
        default=None, description="Version des Generators"
    )


class MatchPreviewItem(BaseModel):
    """Ein Match in der Vorschau."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Dokument-ID")
    document_filename: str = Field(..., description="Dateiname des Dokuments")
    solution_filename: str = Field(..., description="Dateiname in Lösungsdatei")
    solution_position: int = Field(..., description="Position in Lösungsdatei")
    is_valid: bool = Field(..., description="Lösung ist fehlerfrei")
    error_count: int = Field(..., ge=0, description="Anzahl Fehler")
    error_codes: list[str] = Field(
        default_factory=list, description="Liste der Fehler-Codes"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Match-Konfidenz"
    )
    match_reason: str = Field(..., description="Begründung für Match")


class SolutionPreviewResponse(BaseModel):
    """Vorschau der Lösungsdatei-Zuordnung."""

    model_config = ConfigDict(from_attributes=True)

    solution_file_id: str = Field(..., description="ID der Lösungsdatei")
    project_id: str = Field(..., description="Projekt-ID")
    strategy: MatchingStrategy = Field(..., description="Verwendete Matching-Strategie")
    matched_count: int = Field(..., ge=0, description="Anzahl gematchter Dokumente")
    unmatched_documents: int = Field(
        ..., ge=0, description="Anzahl nicht gematchter Dokumente"
    )
    unmatched_solutions: int = Field(
        ..., ge=0, description="Anzahl nicht gematchter Lösungen"
    )
    match_rate: float = Field(..., ge=0.0, le=1.0, description="Match-Rate")
    matches: list[MatchPreviewItem] = Field(..., description="Liste der Matches")
    warnings: list[str] = Field(
        default_factory=list, description="Warnungen bei der Zuordnung"
    )


class ApplyOptionsSchema(BaseModel):
    """Optionen für das Anwenden der Lösungsdatei."""

    model_config = ConfigDict(from_attributes=True)

    strategy: MatchingStrategy = Field(
        default=MatchingStrategy.FILENAME_POSITION,
        description="Matching-Strategie",
    )
    overwrite_existing: bool = Field(
        default=False,
        description="Bestehende manuelle Korrekturen überschreiben",
    )
    min_confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Mindest-Konfidenz für automatische Anwendung",
    )
    create_rag_examples: bool = Field(
        default=True,
        description="RAG-Beispiele aus Lösungen erstellen",
    )
    mark_as_validated: bool = Field(
        default=False,
        description="Dokumente als validiert markieren",
    )


class AppliedCorrectionSchema(BaseModel):
    """Eine angewendete Korrektur."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Dokument-ID")
    document_filename: str = Field(..., description="Dateiname")
    errors_applied: int = Field(..., ge=0, description="Anzahl angewendeter Fehler")
    fields_updated: int = Field(..., ge=0, description="Anzahl aktualisierter Felder")
    rag_examples_created: int = Field(
        ..., ge=0, description="Anzahl erstellter RAG-Beispiele"
    )
    status: str = Field(default="applied", description="Anwendungsstatus")


class SolutionApplyResponse(BaseModel):
    """Response nach Anwenden der Lösungsdatei."""

    model_config = ConfigDict(from_attributes=True)

    solution_file_id: str = Field(..., description="ID der Lösungsdatei")
    project_id: str = Field(..., description="Projekt-ID")
    applied_count: int = Field(..., ge=0, description="Anzahl angewendeter Matches")
    skipped_count: int = Field(..., ge=0, description="Anzahl übersprungener Matches")
    error_count: int = Field(..., ge=0, description="Anzahl Fehler bei Anwendung")
    rag_examples_created: int = Field(
        ..., ge=0, description="Gesamtanzahl erstellter RAG-Beispiele"
    )
    corrections: list[AppliedCorrectionSchema] = Field(
        ..., description="Details der angewendeten Korrekturen"
    )
    errors: list[str] = Field(
        default_factory=list, description="Fehlermeldungen"
    )


class SolutionFileListItem(BaseModel):
    """Lösungsdatei in der Liste."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID")
    project_id: str = Field(..., description="Projekt-ID")
    filename: str = Field(..., description="Dateiname")
    format: SolutionFileFormat = Field(..., description="Format")
    entry_count: int = Field(..., ge=0, description="Anzahl Einträge")
    applied: bool = Field(default=False, description="Wurde angewendet")
    applied_at: datetime | None = Field(default=None, description="Anwendungszeitpunkt")
    created_at: datetime = Field(..., description="Erstellungszeitpunkt")
