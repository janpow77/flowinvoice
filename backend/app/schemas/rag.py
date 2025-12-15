# Pfad: /backend/app/schemas/rag.py
"""
FlowAudit RAG Schemas

Schemas für RAG-Beispiele und Retrieval.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RagExampleSource(BaseModel):
    """RAG-Beispiel Quelle."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str | None = Field(default=None, description="Dokument-ID")
    feedback_id: str | None = Field(default=None, description="Feedback-ID")
    project_id: str | None = Field(default=None, description="Projekt-ID")


class RagExampleMetadata(BaseModel):
    """RAG-Beispiel Metadaten."""

    model_config = ConfigDict(from_attributes=True)

    ruleset_id: str = Field(..., description="Ruleset-ID")
    feature_id: str = Field(..., description="Feature-ID")
    correction_type: str | None = Field(default=None, description="Korrektur-Typ")


class RagExampleContent(BaseModel):
    """RAG-Beispiel Inhalt."""

    model_config = ConfigDict(from_attributes=True)

    original_text_snippet: str | None = Field(default=None, description="Originaltext")
    original_llm_result: dict[str, Any] | None = Field(
        default=None, description="Ursprüngliches LLM-Ergebnis"
    )
    corrected_result: dict[str, Any] | None = Field(
        default=None, description="Korrigiertes Ergebnis"
    )


class RagExampleEmbeddingInfo(BaseModel):
    """RAG-Beispiel Embedding-Info."""

    model_config = ConfigDict(from_attributes=True)

    text_embedded: str | None = Field(default=None, description="Eingebetteter Text")
    embedding_preview: list[float] | None = Field(
        default=None, description="Embedding-Vorschau"
    )
    nearest_neighbors: list[dict[str, Any]] | None = Field(
        default=None, description="Nächste Nachbarn"
    )


class RagExampleUsageStats(BaseModel):
    """RAG-Beispiel Nutzungsstatistik."""

    model_config = ConfigDict(from_attributes=True)

    times_retrieved: int = Field(default=0, description="Mal abgerufen")
    times_helpful: int = Field(default=0, description="Mal hilfreich")
    last_used: datetime | None = Field(default=None, description="Zuletzt verwendet")


class RagExampleResponse(BaseModel):
    """RAG-Beispiel Response."""

    model_config = ConfigDict(from_attributes=True)

    rag_example_id: str = Field(..., alias="id", description="Beispiel-ID")
    created_at: datetime = Field(..., description="Erstellt")
    source: RagExampleSource | None = Field(default=None, description="Quelle")
    metadata: RagExampleMetadata | None = Field(default=None, description="Metadaten")
    content: RagExampleContent | None = Field(default=None, description="Inhalt")
    embedding_info: RagExampleEmbeddingInfo | None = Field(
        default=None, description="Embedding-Info"
    )
    usage_stats: RagExampleUsageStats | None = Field(
        default=None, description="Nutzungsstatistik"
    )


class RagExampleListItem(BaseModel):
    """RAG-Beispiel in Listenansicht."""

    model_config = ConfigDict(from_attributes=True)

    rag_example_id: str = Field(..., description="Beispiel-ID")
    ruleset_id: str = Field(..., description="Ruleset-ID")
    feature_id: str = Field(..., description="Feature-ID")
    correction_type: str | None = Field(default=None, description="Korrektur-Typ")
    similarity_to_nearest: float | None = Field(
        default=None, description="Ähnlichkeit zum nächsten"
    )
    usage_count: int = Field(default=0, description="Nutzungsanzahl")
    created_at: datetime = Field(..., description="Erstellt")


class RagRetrieveRequest(BaseModel):
    """RAG-Retrieval Request."""

    model_config = ConfigDict(from_attributes=True)

    payload_id: str = Field(..., description="Payload-ID")
    top_k: int = Field(default=3, ge=1, le=10, description="Anzahl Ergebnisse")


class RagRetrieveMatch(BaseModel):
    """RAG-Retrieval Match."""

    model_config = ConfigDict(from_attributes=True)

    rag_example_id: str = Field(..., description="Beispiel-ID")
    similarity: float = Field(..., description="Ähnlichkeit (0-1)")
    reason: str | None = Field(default=None, description="Grund")


class RagRetrieveResponse(BaseModel):
    """RAG-Retrieval Response."""

    model_config = ConfigDict(from_attributes=True)

    matches: list[RagRetrieveMatch] = Field(default_factory=list, description="Treffer")
