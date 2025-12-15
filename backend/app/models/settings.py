# Pfad: /backend/app/models/settings.py
"""
FlowAudit Settings Models

Anwendungs-Einstellungen und API-Key-Speicherung.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, LargeBinary, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import Provider


class Setting(Base):
    """
    Anwendungs-Einstellung.

    Key-Value-Speicher für Konfiguration.
    """

    __tablename__ = "settings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Zeitstempel
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<Setting {self.key}>"


class ApiKey(Base):
    """
    Verschlüsselte API-Key-Speicherung.

    Für externe LLM-Provider (OpenAI, Anthropic, Gemini).
    """

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    provider: Mapped[Provider] = mapped_column(
        Enum(Provider), nullable=False, unique=True, index=True
    )

    # Verschlüsselter Key (AES-256 oder Fernet)
    encrypted_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    # Vorschau (letzte 4 Zeichen)
    key_preview: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Status
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    last_tested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<ApiKey {self.provider.value}>"

    @property
    def masked_key(self) -> str | None:
        """Maskierter Key für Anzeige."""
        if self.key_preview:
            return f"{'*' * 32}{self.key_preview}"
        return None
