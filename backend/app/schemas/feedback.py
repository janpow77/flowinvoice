# Pfad: /backend/app/schemas/feedback.py
"""
FlowAudit Feedback Schemas

Schemas für Human-in-the-loop Feedback.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FeedbackRating


class FeedbackOverride(BaseModel):
    """Einzelne Korrektur."""

    model_config = ConfigDict(from_attributes=True)

    feature_id: str = Field(..., description="Feature-ID")
    user_value: Any = Field(..., description="Korrigierter Wert")
    note: str | None = Field(default=None, description="Anmerkung")


class FeedbackCreate(BaseModel):
    """Feedback erstellen."""

    model_config = ConfigDict(from_attributes=True)

    final_result_id: str = Field(..., description="Ergebnis-ID")
    rating: FeedbackRating = Field(..., description="Bewertung")
    comment: str | None = Field(default=None, description="Kommentar")
    overrides: list[FeedbackOverride] = Field(
        default_factory=list, description="Korrekturen"
    )
    accept_result: bool = Field(default=False, description="Ergebnis akzeptieren")


class FeedbackResponse(BaseModel):
    """Feedback Response."""

    model_config = ConfigDict(from_attributes=True)

    feedback_id: str = Field(..., alias="id", description="Feedback-ID")
    document_id: str = Field(..., description="Dokument-ID")
    final_result_id: str | None = Field(default=None, description="Ergebnis-ID")
    rating: FeedbackRating = Field(..., description="Bewertung")
    comment: str | None = Field(default=None, description="Kommentar")
    overrides: list[FeedbackOverride] = Field(
        default_factory=list, description="Korrekturen"
    )
    accept_result: bool = Field(default=False, description="Akzeptiert")
    stored_rag_example_id: str | None = Field(
        default=None, description="Erzeugtes RAG-Beispiel"
    )
    document_status: str | None = Field(default=None, description="Neuer Dokument-Status")
    created_at: datetime = Field(..., description="Erstellt")


class FeedbackListItem(BaseModel):
    """Feedback in Listenansicht."""

    model_config = ConfigDict(from_attributes=True)

    feedback_id: str = Field(..., description="Feedback-ID")
    rating: FeedbackRating = Field(..., description="Bewertung")
    override_count: int = Field(default=0, description="Anzahl Korrekturen")
    created_at: datetime = Field(..., description="Erstellt")
