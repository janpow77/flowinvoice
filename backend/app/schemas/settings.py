# Pfad: /backend/app/schemas/settings.py
"""
FlowAudit Settings Schemas

Schemas für Einstellungen und API-Keys.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from app.models.enums import Provider


class OllamaModel(BaseModel):
    """Ollama-Modell Info."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Modellname")
    size_gb: float = Field(..., description="Größe in GB")
    loaded: bool = Field(default=False, description="Geladen")
    modified_at: str | None = Field(default=None, description="Geändert")


class OllamaModelsResponse(BaseModel):
    """Ollama-Modelle Response."""

    model_config = ConfigDict(from_attributes=True)

    models: list[OllamaModel] = Field(default_factory=list, description="Modelle")


class ProviderSettings(BaseModel):
    """Provider-spezifische Einstellungen."""

    model_config = ConfigDict(from_attributes=True)

    enabled: bool = Field(default=False, description="Aktiviert")
    base_url: str | None = Field(default=None, description="Basis-URL (Ollama)")
    api_key_is_set: bool = Field(default=False, description="API-Key gesetzt")
    api_key_masked: str | None = Field(default=None, description="Maskierter API-Key")
    model_name: str | None = Field(default=None, description="Aktives Modell")
    available_models: list[str] = Field(
        default_factory=list, description="Verfügbare Modelle"
    )


class InferenceSettings(BaseModel):
    """Inferenz-Einstellungen."""

    model_config = ConfigDict(from_attributes=True)

    temperature: float = Field(
        default=0.2, ge=0.0, le=1.5, description="Temperature"
    )
    max_tokens: int = Field(
        default=2000, ge=64, le=8192, description="Max Tokens"
    )
    timeout_sec: int = Field(
        default=120, ge=30, le=300, description="Timeout (Sekunden)"
    )
    parallel_requests: int = Field(
        default=2, ge=1, le=10, description="Parallele Requests"
    )
    retry_on_error: bool = Field(default=True, description="Retry bei Fehler")
    max_retries: int = Field(default=3, ge=0, le=10, description="Max Retries")


class GeneratorSettings(BaseModel):
    """Generator-Einstellungen."""

    model_config = ConfigDict(from_attributes=True)

    output_dir: str = Field(default="/data/exports", description="Ausgabeverzeichnis")
    solutions_dir: str = Field(default="/data/exports", description="Lösungsverzeichnis")
    enable_admin_menu: bool = Field(default=True, description="Admin-Menü aktiviert")


class RagSettings(BaseModel):
    """RAG-Einstellungen."""

    model_config = ConfigDict(from_attributes=True)

    enabled: bool = Field(default=True, description="RAG aktiviert")
    top_k: int = Field(default=3, ge=1, le=10, description="Top-K Ergebnisse")
    similarity_threshold: float = Field(
        default=0.25, ge=0.0, le=1.0, description="Ähnlichkeitsschwelle"
    )


class LoggingSettings(BaseModel):
    """Logging-Einstellungen."""

    model_config = ConfigDict(from_attributes=True)

    verbose: bool = Field(default=False, description="Ausführliches Logging")


class SettingsResponse(BaseModel):
    """Vollständige Einstellungen."""

    model_config = ConfigDict(from_attributes=True)

    active_provider: Provider = Field(..., description="Aktiver Provider")
    providers: dict[str, ProviderSettings] = Field(..., description="Provider-Settings")
    inference: InferenceSettings = Field(..., description="Inferenz-Settings")
    generator: GeneratorSettings = Field(..., description="Generator-Settings")
    rag: RagSettings = Field(..., description="RAG-Settings")
    logging: LoggingSettings = Field(..., description="Logging-Settings")


class SettingsUpdate(BaseModel):
    """Einstellungen aktualisieren."""

    model_config = ConfigDict(from_attributes=True)

    active_provider: Provider | None = None
    providers: dict[str, dict[str, Any]] | None = None
    inference: dict[str, Any] | None = None
    generator: dict[str, Any] | None = None
    rag: dict[str, Any] | None = None
    logging: dict[str, Any] | None = None


class ApiKeySet(BaseModel):
    """API-Key setzen."""

    model_config = ConfigDict(from_attributes=True)

    api_key: SecretStr = Field(..., description="API-Key")


class ApiKeyResponse(BaseModel):
    """API-Key Response."""

    model_config = ConfigDict(from_attributes=True)

    provider: Provider = Field(..., description="Provider")
    api_key_is_set: bool = Field(..., description="API-Key gesetzt")
    api_key_masked: str | None = Field(default=None, description="Maskierter Key")


class ProviderTestResponse(BaseModel):
    """Provider-Test Response."""

    model_config = ConfigDict(from_attributes=True)

    provider: Provider = Field(..., description="Provider")
    status: str = Field(..., description="ok | error")
    model_accessible: bool = Field(default=False, description="Modell erreichbar")
    latency_ms: int | None = Field(default=None, description="Latenz (ms)")
    message: str | None = Field(default=None, description="Nachricht")


class ModelPullRequest(BaseModel):
    """Modell-Pull Request."""

    model_config = ConfigDict(from_attributes=True)

    model_name: str = Field(..., description="Modellname")


class ModelPullResponse(BaseModel):
    """Modell-Pull Response."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="pulling | done | error")
    model_name: str = Field(..., description="Modellname")
    progress_url: str | None = Field(default=None, description="Progress-URL")
