# Pfad: /backend/app/models/user.py
"""
FlowAudit User Model

Datenbankmodell für Benutzer gemäß Nutzerkonzept.
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class User(Base):
    """
    Benutzer-Modell für FlowAudit.

    Rollen:
    - admin: Systemverwaltung, Nutzerverwaltung, voller Zugriff
    - schueler: Arbeitet an zugewiesenem Projekt, sieht nur eigenes Projekt
    - extern: Eingeschränkter Gastzugang, nur freigegebene Projekte + Generator
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
    theme: Mapped[str] = mapped_column(
        String(10),
        default="system",
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        default="schueler",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Projekt-Zuweisung (für Schüler: das Projekt an dem sie arbeiten)
    assigned_project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_project: Mapped["Project | None"] = relationship(
        "Project",
        foreign_keys=[assigned_project_id],
        back_populates="assigned_users",
    )

    # Für Extern-Zugang: Zeitbegrenzung
    access_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )

    # Wer hat diesen Nutzer eingeladen (für Audit-Trail)
    invited_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    invited_by: Mapped["User | None"] = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[invited_by_id],
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

    @property
    def is_admin(self) -> bool:
        """Prüft, ob der Nutzer Admin ist."""
        return self.role == "admin"

    @property
    def is_schueler(self) -> bool:
        """Prüft, ob der Nutzer ein Schüler ist."""
        return self.role == "schueler"

    @property
    def is_extern(self) -> bool:
        """Prüft, ob der Nutzer extern ist."""
        return self.role == "extern"

    @property
    def has_valid_access(self) -> bool:
        """Prüft, ob der Zugang noch gültig ist (relevant für Externe)."""
        if not self.is_active:
            return False
        if self.access_expires_at and datetime.now(UTC) > self.access_expires_at:
            return False
        return True
