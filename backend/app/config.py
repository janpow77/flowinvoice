# Pfad: /backend/app/config.py
"""
FlowAudit Configuration

Zentrale Konfiguration für alle Komponenten des Systems.
Verwendet pydantic-settings für Umgebungsvariablen-Validierung.
"""

import logging
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Zentrale Anwendungskonfiguration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "FlowAudit"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    secret_key: SecretStr = Field(default="flowaudit_dev_secret_key_change_in_production")

    # CORS - Erlaubte Origins (kommasepariert)
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Kommaseparierte Liste erlaubter CORS-Origins"
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://flowaudit:flowaudit_secret@localhost:5432/flowaudit"
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ChromaDB (Vector Store)
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_token: str = "flowaudit_chroma_token"
    chroma_collection_name: str = "flowaudit_corrections"

    # Ollama (Local LLM)
    ollama_host: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.1:8b-instruct-q4"
    ollama_timeout_sec: int = 120

    # External LLM Providers (optional)
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None

    # Default inference settings
    default_temperature: float = 0.2
    default_max_tokens: int = 2000
    default_timeout_sec: int = 120

    # Storage paths
    storage_path: Path = Field(default=Path("/data"))
    uploads_dir: str = "uploads"
    exports_dir: str = "exports"
    previews_dir: str = "previews"
    logs_dir: str = "logs"

    # RAG settings
    rag_enabled: bool = True
    rag_top_k: int = 3
    rag_similarity_threshold: float = 0.25
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Parser settings
    parser_timeout_sec: int = 30
    parser_max_pages: int = 50

    # Generator settings
    generator_enabled: bool = True
    generator_max_count: int = 100

    # API Authentication
    # Setzen Sie ADMIN_API_KEY für Produktionsumgebungen
    admin_api_key: SecretStr | None = Field(
        default=None,
        description="API-Key für Admin-Endpoints (Generator, etc.). Muss in Produktion gesetzt werden."
    )

    # JWT Authentication
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # Demo-Benutzer (für Entwicklung/Seminare - in Produktion deaktivieren!)
    # Format: "username:password_hash" (bcrypt) oder "username:plaintext" im Debug-Modus
    demo_users: str = Field(
        default="admin:admin,user:user",
        description="Kommaseparierte Liste von Demo-Benutzern (username:password)"
    )

    # Performance / Worker settings
    uvicorn_workers: int = Field(default=4, ge=1, le=8)
    celery_concurrency: int = Field(default=4, ge=1, le=8)

    @field_validator("storage_path", mode="before")
    @classmethod
    def validate_storage_path(cls, v: str | Path) -> Path:
        """Konvertiert String zu Path."""
        return Path(v) if isinstance(v, str) else v

    @property
    def uploads_path(self) -> Path:
        """Vollständiger Pfad für Uploads."""
        return self.storage_path / self.uploads_dir

    @property
    def exports_path(self) -> Path:
        """Vollständiger Pfad für Exports."""
        return self.storage_path / self.exports_dir

    @property
    def previews_path(self) -> Path:
        """Vollständiger Pfad für Template-Previews."""
        return self.storage_path / self.previews_dir

    @property
    def logs_path(self) -> Path:
        """Vollständiger Pfad für Logs."""
        return self.storage_path / self.logs_dir

    @property
    def cors_origins_list(self) -> list[str]:
        """Liste der erlaubten CORS-Origins."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Validiert und warnt bei unsicheren Default-Einstellungen."""
        issues: list[str] = []

        # Secret Key prüfen
        default_key = "flowaudit_dev_secret_key_change_in_production"
        if self.secret_key.get_secret_value() == default_key:
            issues.append("SECRET_KEY verwendet den Default-Wert")

        # Database URL prüfen (enthält Default-Credentials?)
        default_db_url = "postgresql+asyncpg://flowaudit:flowaudit_secret@localhost:5432/flowaudit"
        if self.database_url == default_db_url:
            issues.append("DATABASE_URL verwendet Default-Credentials")

        # Chroma Token prüfen
        if self.chroma_token == "flowaudit_chroma_token":
            issues.append("CHROMA_TOKEN verwendet den Default-Wert")

        # CORS mit Credentials und Wildcard prüfen
        if self.cors_origins == "*":
            issues.append(
                "CORS_ORIGINS ist auf '*' gesetzt - dies ist unsicher mit Credentials. "
                "Setzen Sie explizite Origins für Produktion."
            )

        # Warnungen ausgeben wenn nicht im Debug-Modus
        if issues and not self.debug:
            for issue in issues:
                warning_msg = f"SICHERHEITSWARNUNG: {issue}"
                warnings.warn(warning_msg, UserWarning, stacklevel=2)
                logger.warning(warning_msg)

        return self

    @property
    def is_production_ready(self) -> bool:
        """Prüft ob die Konfiguration für Produktion geeignet ist."""
        default_key = "flowaudit_dev_secret_key_change_in_production"
        default_db_url = "postgresql+asyncpg://flowaudit:flowaudit_secret@localhost:5432/flowaudit"

        return (
            self.secret_key.get_secret_value() != default_key
            and self.database_url != default_db_url
            and self.chroma_token != "flowaudit_chroma_token"
            and self.cors_origins != "*"
        )


class RetryConfig(BaseSettings):
    """Retry-Konfiguration für verschiedene Operationen."""

    model_config = SettingsConfigDict(env_prefix="RETRY_")

    # PDF Parser
    pdf_parse_max_retries: int = 1
    pdf_parse_timeout_sec: int = 30

    # LLM Calls
    llm_max_retries: int = 3
    llm_base_delay_sec: int = 2
    llm_max_delay_sec: int = 30
    llm_timeout_sec: int = 120

    # Database Operations
    db_max_retries: int = 3
    db_delay_sec: int = 1
    db_timeout_sec: int = 10

    # External API (rate limited)
    external_api_max_retries: int = 3
    external_api_base_delay_sec: int = 5
    external_api_max_delay_sec: int = 60
    external_api_respect_rate_limit: bool = True


class HealthCheckConfig(BaseSettings):
    """Health-Check-Konfiguration für Services."""

    model_config = SettingsConfigDict(env_prefix="HEALTH_")

    db_interval_sec: int = 30
    db_timeout_sec: int = 5
    db_unhealthy_threshold: int = 3

    ollama_interval_sec: int = 60
    ollama_timeout_sec: int = 10
    ollama_unhealthy_threshold: int = 2

    chroma_interval_sec: int = 60
    chroma_timeout_sec: int = 5
    chroma_unhealthy_threshold: int = 3

    redis_interval_sec: int = 30
    redis_timeout_sec: int = 5
    redis_unhealthy_threshold: int = 2


@lru_cache
def get_settings() -> Settings:
    """Gibt gecachte Settings-Instanz zurück."""
    return Settings()


@lru_cache
def get_retry_config() -> RetryConfig:
    """Gibt gecachte RetryConfig-Instanz zurück."""
    return RetryConfig()


@lru_cache
def get_health_config() -> HealthCheckConfig:
    """Gibt gecachte HealthCheckConfig-Instanz zurück."""
    return HealthCheckConfig()
