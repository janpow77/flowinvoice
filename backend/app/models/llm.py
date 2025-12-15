# Pfad: /backend/app/models/llm.py
"""
FlowAudit LLM Models

PreparePayload (Input-JSON), LLM-Runs und Logs.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import Provider

if TYPE_CHECKING:
    from app.models.document import Document


class PreparePayload(Base):
    """
    Vorbereitetes Payload für LLM-Anfrage.

    Dies ist das INPUT-JSON, das an die KI übergeben wird.
    MUSS persistiert und in der UI angezeigt werden.
    """

    __tablename__ = "prepare_payloads"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )

    # Schema-Version
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0")

    # Ruleset-Info
    ruleset: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    ui_language: Mapped[str] = mapped_column(String(5), nullable=False)

    # Kontext
    project_context: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    parsing_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    deterministic_precheck_results: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Features (zu prüfende Merkmale)
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Extrahierter Text
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Schema für Output
    required_output_schema: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # RAG-Kontext (Few-Shot-Beispiele)
    rag_context: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="payloads")
    llm_runs: Mapped[list["LlmRun"]] = relationship(
        "LlmRun", back_populates="payload", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<PreparePayload {self.id[:8]} v{self.schema_version}>"


class LlmRun(Base):
    """
    LLM-Ausführung (Inference).

    Speichert Request, Response, Timing und Token-Usage.
    """

    __tablename__ = "llm_runs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    payload_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("prepare_payloads.id"), nullable=True
    )

    # Provider und Modell
    provider: Mapped[Provider] = mapped_column(Enum(Provider), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    # Timing und Tokens
    timings_ms: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Response
    raw_response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Fehler
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="llm_runs")
    payload: Mapped["PreparePayload | None"] = relationship(
        "PreparePayload", back_populates="llm_runs"
    )
    logs: Mapped[list["LlmRunLog"]] = relationship(
        "LlmRunLog", back_populates="llm_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<LlmRun {self.id[:8]} [{self.provider.value}:{self.model_name}]>"

    @property
    def duration_ms(self) -> int | None:
        """Gesamtdauer in Millisekunden."""
        if self.timings_ms:
            return self.timings_ms.get("llm") or self.timings_ms.get("total")
        return None

    @property
    def input_tokens(self) -> int | None:
        """Input-Tokens."""
        if self.token_usage:
            return self.token_usage.get("input")
        return None

    @property
    def output_tokens(self) -> int | None:
        """Output-Tokens."""
        if self.token_usage:
            return self.token_usage.get("output")
        return None

    def get_feature_result(self, feature_id: str) -> dict[str, Any] | None:
        """
        Gibt Feature-Ergebnis aus Response zurück.

        Args:
            feature_id: Feature-ID.

        Returns:
            Feature-Ergebnis-Dict oder None.
        """
        if not self.structured_response:
            return None

        features: list[dict[str, Any]] = self.structured_response.get("features", [])
        for feature in features:
            if feature.get("feature_id") == feature_id:
                return feature
        return None


class LlmRunLog(Base):
    """
    Log-Eintrag für LLM-Run.

    Für LogView in der UI.
    """

    __tablename__ = "llm_run_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    llm_run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("llm_runs.id", ondelete="CASCADE"), nullable=False
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    llm_run: Mapped["LlmRun"] = relationship("LlmRun", back_populates="logs")

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<LlmRunLog [{self.level}] {self.message[:30]}>"
