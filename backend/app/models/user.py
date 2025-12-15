# Pfad: /backend/app/models/user.py
"""
FlowAudit User Model

Datenbankmodell für Benutzer gemäß Nutzerkonzept.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """
    Benutzer-Modell für FlowAudit.

    Rollen:
    - admin: Systemverwaltung, Nutzerverwaltung
    - user: Projekte, Dokumente, Prüfungen
    """

    __tablename__ = "users"

    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Login & Auth
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Stammdaten
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    organization: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    contact_info: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Einstellungen & Status
    language: Mapped[str] = mapped_column(
        String(5),
        default="de",
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Tracking (Throttled - max. alle 5 Min aktualisiert)
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
