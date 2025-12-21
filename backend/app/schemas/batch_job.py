"""
Schemas für Batch-Jobs.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.enums import BatchJobStatus


class BatchJobCreate(BaseModel):
    """Schema für das Erstellen eines Batch-Jobs."""

    job_type: str = Field(..., description="Job-Typ (BATCH_ANALYZE, BATCH_VALIDATE, etc.)")
    project_id: Optional[str] = Field(None, description="Projekt-ID")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Job-Parameter")
    priority: int = Field(0, ge=-10, le=10, description="Priorität (-10 bis 10)")
    scheduled_at: Optional[datetime] = Field(None, description="Geplante Ausführungszeit")


class BatchJobUpdate(BaseModel):
    """Schema für das Aktualisieren eines Batch-Jobs."""

    status: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    priority: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class BatchJobProgress(BaseModel):
    """Schema für Fortschritt eines Batch-Jobs."""

    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    progress_percent: float = 0.0
    status_message: Optional[str] = None


class BatchJobResponse(BaseModel):
    """Schema für die Antwort eines Batch-Jobs."""

    id: str
    job_type: str
    project_id: Optional[str]
    status: str
    created_by_id: Optional[str]
    parameters: dict[str, Any]
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    skipped_items: int
    progress_percent: float
    results: dict[str, Any]
    errors: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    status_message: Optional[str]
    celery_task_id: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    scheduled_at: Optional[datetime]
    is_scheduled: bool
    priority: int

    class Config:
        from_attributes = True


class BatchJobListItem(BaseModel):
    """Schema für Batch-Job in einer Liste."""

    id: str
    job_type: str
    project_id: Optional[str]
    status: str
    total_items: int
    processed_items: int
    progress_percent: float
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    is_scheduled: bool
    priority: int

    class Config:
        from_attributes = True


class BatchJobListResponse(BaseModel):
    """Response für Batch-Job-Liste."""

    jobs: list[BatchJobListItem]
    total: int


# Job-Typ-spezifische Schemas

class BatchAnalyzeParams(BaseModel):
    """Parameter für Batch-Analyse."""

    document_ids: Optional[list[str]] = Field(None, description="Spezifische Dokument-IDs")
    status_filter: Optional[list[str]] = Field(None, description="Status-Filter")
    provider: Optional[str] = Field(None, description="LLM-Provider")
    model: Optional[str] = Field(None, description="LLM-Modell")
    max_concurrent: int = Field(5, ge=1, le=20, description="Max parallele Analysen")


class BatchValidateParams(BaseModel):
    """Parameter für Batch-Validierung."""

    document_ids: Optional[list[str]] = None
    revalidate: bool = Field(False, description="Bereits validierte erneut prüfen")


class BatchExportParams(BaseModel):
    """Parameter für Batch-Export."""

    format: str = Field("CSV", description="Export-Format (CSV, XLSX, JSON)")
    include_fields: Optional[list[str]] = None
    include_errors: bool = True
    include_analysis: bool = True


class SolutionApplyParams(BaseModel):
    """Parameter für Lösungsdatei-Anwendung."""

    solution_file_id: str
    strategy: str = Field("FILENAME", description="Matching-Strategie")
    min_confidence: float = Field(0.7, ge=0.0, le=1.0)
    overwrite_existing: bool = False
    create_rag_examples: bool = True


class RagRebuildParams(BaseModel):
    """Parameter für RAG-Index-Neuaufbau."""

    clear_existing: bool = Field(False, description="Bestehenden Index löschen")
    include_feedback: bool = True
    include_examples: bool = True
