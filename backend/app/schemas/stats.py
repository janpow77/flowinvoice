# Pfad: /backend/app/schemas/stats.py
"""
FlowAudit Statistics Schemas

Schemas für Statistik-Dashboard und Auswertungen.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Overview(BaseModel):
    """Übersicht-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    total_analyses: int = Field(default=0, description="Gesamtanalysen")
    total_projects: int = Field(default=0, description="Projekte")
    total_documents: int = Field(default=0, description="Dokumente")
    total_rag_examples: int = Field(default=0, description="RAG-Beispiele")
    session_analyses: int = Field(default=0, description="Session-Analysen")
    uptime_hours: float = Field(default=0.0, description="Uptime (Stunden)")


class Accuracy(BaseModel):
    """Genauigkeits-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    overall_accuracy_percent: float = Field(default=0.0, description="Gesamtgenauigkeit")
    feature_accuracy: dict[str, float] = Field(
        default_factory=dict, description="Feature-Genauigkeit"
    )


class ProviderStats(BaseModel):
    """Provider-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    count: int = Field(default=0, description="Anzahl")
    avg_time_ms: int = Field(default=0, description="Durchschnittliche Zeit (ms)")


class TimeTrendPoint(BaseModel):
    """Zeitreihen-Datenpunkt."""

    model_config = ConfigDict(from_attributes=True)

    date: str = Field(..., description="Datum")
    count: int = Field(default=0, description="Anzahl")
    accuracy: float = Field(default=0.0, description="Genauigkeit")


class TimeTrend(BaseModel):
    """Zeitreihen-Trend."""

    model_config = ConfigDict(from_attributes=True)

    period: str = Field(default="7d", description="Zeitraum")
    data_points: list[TimeTrendPoint] = Field(
        default_factory=list, description="Datenpunkte"
    )


class GlobalStatsResponse(BaseModel):
    """Globale Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    overview: Overview = Field(..., description="Übersicht")
    accuracy: Accuracy = Field(..., description="Genauigkeit")
    by_provider: dict[str, ProviderStats] = Field(
        default_factory=dict, description="Nach Provider"
    )
    time_trend: TimeTrend | None = Field(default=None, description="Zeittrend")


class ProjectCounters(BaseModel):
    """Projekt-Zähler."""

    model_config = ConfigDict(from_attributes=True)

    documents_total: int = Field(default=0, description="Dokumente")
    accepted: int = Field(default=0, description="Akzeptiert")
    review_pending: int = Field(default=0, description="In Review")
    rejected: int = Field(default=0, description="Abgelehnt")
    rag_examples_used: int = Field(default=0, description="RAG-Beispiele genutzt")


class Timings(BaseModel):
    """Timing-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    avg_parse_ms: int = Field(default=0, description="Durchschnitt Parse (ms)")
    avg_llm_ms: int = Field(default=0, description="Durchschnitt LLM (ms)")
    avg_total_ms: int = Field(default=0, description="Durchschnitt Gesamt (ms)")


class Tokens(BaseModel):
    """Token-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    avg_in: int = Field(default=0, description="Durchschnitt Input")
    avg_out: int = Field(default=0, description="Durchschnitt Output")


class FeatureErrorRate(BaseModel):
    """Feature-Fehlerrate."""

    model_config = ConfigDict(from_attributes=True)

    feature_id: str = Field(..., description="Feature-ID")
    missing_rate: float = Field(default=0.0, description="Fehlend-Rate")
    unclear_rate: float = Field(default=0.0, description="Unklar-Rate")


class ProjectStatsResponse(BaseModel):
    """Projekt-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    project_id: str = Field(..., description="Projekt-ID")
    counters: ProjectCounters = Field(..., description="Zähler")
    timings: Timings = Field(..., description="Timing")
    tokens: Tokens = Field(..., description="Tokens")
    feature_error_rates: list[FeatureErrorRate] = Field(
        default_factory=list, description="Feature-Fehlerraten"
    )


class RatingDistribution(BaseModel):
    """Bewertungsverteilung."""

    model_config = ConfigDict(from_attributes=True)

    CORRECT: int = Field(default=0, description="Korrekt")
    PARTIAL: int = Field(default=0, description="Teilweise")
    WRONG: int = Field(default=0, description="Falsch")


class FeedbackSummary(BaseModel):
    """Feedback-Zusammenfassung."""

    model_config = ConfigDict(from_attributes=True)

    total_feedback_entries: int = Field(default=0, description="Gesamt")
    rating_distribution: RatingDistribution = Field(..., description="Verteilung")
    avg_corrections_per_analysis: float = Field(
        default=0.0, description="Durchschnitt Korrekturen"
    )


class ErrorByFeature(BaseModel):
    """Fehler nach Feature."""

    model_config = ConfigDict(from_attributes=True)

    feature_id: str = Field(..., description="Feature-ID")
    total_errors: int = Field(default=0, description="Fehler gesamt")
    error_types: dict[str, int] = Field(
        default_factory=dict, description="Fehlertypen"
    )
    most_common_correction: str | None = Field(
        default=None, description="Häufigste Korrektur"
    )


class TaxLawErrorBreakdown(BaseModel):
    """Detaillierte Steuerrecht-Fehler."""

    model_config = ConfigDict(from_attributes=True)

    type: str = Field(..., description="Fehlertyp")
    count: int = Field(default=0, description="Anzahl")
    label_de: str = Field(..., description="Label (DE)")
    label_en: str = Field(..., description="Label (EN)")
    example: str | None = Field(default=None, description="Beispiel")


class TaxLawFeatureDetail(BaseModel):
    """Steuerrecht Feature-Detail."""

    model_config = ConfigDict(from_attributes=True)

    feature_id: str = Field(..., description="Feature-ID")
    name_de: str = Field(..., description="Name (DE)")
    name_en: str = Field(..., description="Name (EN)")
    legal_basis: str = Field(..., description="Rechtsgrundlage")
    total_errors: int = Field(default=0, description="Fehler gesamt")
    error_breakdown: list[TaxLawErrorBreakdown] = Field(
        default_factory=list, description="Fehler-Aufschlüsselung"
    )


class ErrorBySource(BaseModel):
    """Fehler nach Quelle."""

    model_config = ConfigDict(from_attributes=True)

    label_de: str = Field(..., description="Label (DE)")
    label_en: str = Field(..., description="Label (EN)")
    total_errors: int = Field(default=0, description="Fehler gesamt")
    percentage: float = Field(default=0.0, description="Prozent")
    features: list[dict[str, Any]] = Field(
        default_factory=list, description="Features"
    )
    detail: list[TaxLawFeatureDetail] | None = Field(
        default=None, description="Detail (nur TAX_LAW)"
    )


class RagImprovement(BaseModel):
    """RAG-Verbesserung."""

    model_config = ConfigDict(from_attributes=True)

    accuracy_before_rag: float = Field(default=0.0, description="Vor RAG")
    accuracy_after_rag: float = Field(default=0.0, description="Nach RAG")
    improvement_percent: float = Field(default=0.0, description="Verbesserung")
    examples_contributing: int = Field(default=0, description="Beitragende Beispiele")


class FeedbackTimelinePoint(BaseModel):
    """Feedback-Timeline Punkt."""

    model_config = ConfigDict(from_attributes=True)

    date: str = Field(..., description="Datum")
    correct: int = Field(default=0, description="Korrekt")
    partial: int = Field(default=0, description="Teilweise")
    wrong: int = Field(default=0, description="Falsch")


class FeedbackStatsResponse(BaseModel):
    """Feedback-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    summary: FeedbackSummary = Field(..., description="Zusammenfassung")
    errors_by_feature: list[ErrorByFeature] = Field(
        default_factory=list, description="Fehler nach Feature"
    )
    errors_by_source: dict[str, ErrorBySource] = Field(
        default_factory=dict, description="Fehler nach Quelle"
    )
    rag_improvement: RagImprovement | None = Field(
        default=None, description="RAG-Verbesserung"
    )
    feedback_timeline: list[FeedbackTimelinePoint] = Field(
        default_factory=list, description="Timeline"
    )


class LocalModelStats(BaseModel):
    """Lokale Modell-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    model_name: str = Field(..., description="Modellname")
    model_size_gb: float = Field(default=0.0, description="Größe (GB)")
    quantization: str | None = Field(default=None, description="Quantisierung")
    loaded: bool = Field(default=False, description="Geladen")
    context_window: int = Field(default=0, description="Kontextfenster")
    total_requests: int = Field(default=0, description="Anfragen gesamt")
    avg_tokens_in: int = Field(default=0, description="Durchschnitt Tokens In")
    avg_tokens_out: int = Field(default=0, description="Durchschnitt Tokens Out")
    total_tokens_processed: int = Field(default=0, description="Tokens gesamt")
    avg_inference_time_ms: int = Field(default=0, description="Durchschnitt Zeit (ms)")
    min_inference_time_ms: int = Field(default=0, description="Min Zeit (ms)")
    max_inference_time_ms: int = Field(default=0, description="Max Zeit (ms)")
    tokens_per_second_avg: float = Field(
        default=0.0, description="Tokens pro Sekunde"
    )


class ResourceUsage(BaseModel):
    """Ressourcen-Nutzung."""

    model_config = ConfigDict(from_attributes=True)

    current_cpu_percent: float = Field(default=0.0, description="CPU %")
    current_ram_mb: int = Field(default=0, description="RAM (MB)")
    current_ram_percent: float = Field(default=0.0, description="RAM %")
    gpu_available: bool = Field(default=False, description="GPU verfügbar")
    gpu_name: str | None = Field(default=None, description="GPU-Name")
    gpu_memory_used_mb: int = Field(default=0, description="GPU-Speicher (MB)")
    gpu_memory_total_mb: int = Field(default=0, description="GPU-Speicher gesamt (MB)")
    gpu_utilization_percent: float = Field(default=0.0, description="GPU %")


class ErrorStats(BaseModel):
    """Fehler-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    timeout_count: int = Field(default=0, description="Timeouts")
    parse_error_count: int = Field(default=0, description="Parse-Fehler")
    connection_error_count: int = Field(default=0, description="Verbindungsfehler")
    last_error: dict[str, Any] | None = Field(default=None, description="Letzter Fehler")


class ExternalProviderStats(BaseModel):
    """Externe Provider-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    total_requests: int = Field(default=0, description="Anfragen")
    total_tokens: int = Field(default=0, description="Tokens")
    avg_latency_ms: int = Field(default=0, description="Latenz (ms)")
    estimated_cost_usd: float = Field(default=0.0, description="Geschätzte Kosten ($)")


class LlmStatsResponse(BaseModel):
    """LLM-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    active_provider: str = Field(..., description="Aktiver Provider")
    active_model: str = Field(..., description="Aktives Modell")
    local_model_stats: LocalModelStats | None = Field(
        default=None, description="Lokale Modell-Stats"
    )
    resource_usage: ResourceUsage | None = Field(
        default=None, description="Ressourcen-Nutzung"
    )
    error_stats: ErrorStats | None = Field(default=None, description="Fehler-Stats")
    external_providers: dict[str, ExternalProviderStats] = Field(
        default_factory=dict, description="Externe Provider"
    )


class CollectionStats(BaseModel):
    """ChromaDB Collection-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    collection_name: str = Field(..., description="Collection-Name")
    total_examples: int = Field(default=0, description="Beispiele")
    embedding_model: str = Field(..., description="Embedding-Modell")
    embedding_dimension: int = Field(default=384, description="Dimension")
    storage_size_mb: float = Field(default=0.0, description="Größe (MB)")


class RetrievalStats(BaseModel):
    """Retrieval-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    total_retrievals: int = Field(default=0, description="Abrufe")
    avg_similarity_score: float = Field(default=0.0, description="Durchschnitt Ähnlichkeit")
    cache_hit_rate: float = Field(default=0.0, description="Cache-Trefferrate")


class RecentRagExample(BaseModel):
    """Kürzliches RAG-Beispiel."""

    model_config = ConfigDict(from_attributes=True)

    rag_example_id: str = Field(..., description="ID")
    created_at: datetime = Field(..., description="Erstellt")
    ruleset_id: str = Field(..., description="Ruleset")
    feature_id: str = Field(..., description="Feature")
    correction_type: str | None = Field(default=None, description="Korrektur-Typ")
    similarity_to_nearest: float = Field(default=0.0, description="Ähnlichkeit")
    usage_count: int = Field(default=0, description="Nutzung")


class RagStatsResponse(BaseModel):
    """RAG-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    collection_stats: CollectionStats = Field(..., description="Collection-Stats")
    by_ruleset: dict[str, int] = Field(default_factory=dict, description="Nach Ruleset")
    by_feature: list[dict[str, Any]] = Field(
        default_factory=list, description="Nach Feature"
    )
    retrieval_stats: RetrievalStats = Field(..., description="Retrieval-Stats")
    recent_examples: list[RecentRagExample] = Field(
        default_factory=list, description="Kürzliche Beispiele"
    )


class ComponentStatus(BaseModel):
    """Komponenten-Status."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="ok | error | degraded")
    version: str | None = Field(default=None, description="Version")
    uptime_sec: int | None = Field(default=None, description="Uptime (s)")
    type: str | None = Field(default=None, description="Typ")
    connections_active: int | None = Field(default=None, description="Verbindungen")
    connections_max: int | None = Field(default=None, description="Max Verbindungen")
    models_loaded: int | None = Field(default=None, description="Modelle geladen")
    collections: int | None = Field(default=None, description="Collections")
    memory_used_mb: int | None = Field(default=None, description="Speicher (MB)")


class Storage(BaseModel):
    """Speicher-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    db_size_mb: float = Field(default=0.0, description="DB (MB)")
    uploads_size_mb: float = Field(default=0.0, description="Uploads (MB)")
    generated_size_mb: float = Field(default=0.0, description="Generiert (MB)")
    vectorstore_size_mb: float = Field(default=0.0, description="Vectorstore (MB)")
    logs_size_mb: float = Field(default=0.0, description="Logs (MB)")
    total_used_mb: float = Field(default=0.0, description="Gesamt (MB)")
    disk_free_mb: float = Field(default=0.0, description="Frei (MB)")


class ActivityLogEntry(BaseModel):
    """Aktivitätslog-Eintrag."""

    model_config = ConfigDict(from_attributes=True)

    ts: datetime = Field(..., description="Zeitstempel")
    event: str = Field(..., description="Ereignis")
    detail: str | None = Field(default=None, description="Detail")


class SystemStatsResponse(BaseModel):
    """System-Statistiken."""

    model_config = ConfigDict(from_attributes=True)

    components: dict[str, ComponentStatus] = Field(
        default_factory=dict, description="Komponenten"
    )
    storage: Storage = Field(..., description="Speicher")
    activity_log: list[ActivityLogEntry] = Field(
        default_factory=list, description="Aktivitätslog"
    )
