# Pfad: /backend/app/models/project_share.py
"""
FlowAudit Project Share Model

Modell für granulare Projektfreigaben an externe Nutzer.
"""

import secrets
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class ProjectShare(Base):
    """
    Projektfreigabe für externe Nutzer.

    Ermöglicht granulare Freigabe von Projekten:
    - An spezifische Nutzer (user_id gesetzt)
    - Per Link (share_token gesetzt, user_id null)

    Berechtigungen:
    - read: Nur lesen
    - write: Lesen und bearbeiten (für zukünftige Erweiterungen)
    """

    __tablename__ = "project_shares"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Projekt, das freigegeben wird
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project: Mapped["Project"] = relationship("Project")

    # Optional: Nutzer, für den freigegeben wird (null bei Link-Freigaben)
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id])

    # Art der Freigabe: "user" oder "link"
    share_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Token für Link-basierte Freigaben
    share_token: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
    )

    # Berechtigungsstufe: "read" oder "write"
    permissions: Mapped[str] = mapped_column(
        String(20),
        default="read",
        nullable=False,
    )

    # Optionales Ablaufdatum
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Audit-Felder
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    created_by_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self) -> str:
        return f"<ProjectShare(project={self.project_id}, type={self.share_type})>"

    @classmethod
    def create_user_share(
        cls,
        project_id: str,
        user_id: str,
        created_by_id: str,
        permissions: str = "read",
        expires_at: datetime | None = None,
    ) -> "ProjectShare":
        """Erstellt eine Nutzer-spezifische Freigabe."""
        return cls(
            project_id=project_id,
            user_id=user_id,
            share_type="user",
            permissions=permissions,
            expires_at=expires_at,
            created_by_id=created_by_id,
        )

    @classmethod
    def create_link_share(
        cls,
        project_id: str,
        created_by_id: str,
        permissions: str = "read",
        expires_at: datetime | None = None,
    ) -> "ProjectShare":
        """Erstellt eine Link-basierte Freigabe."""
        return cls(
            project_id=project_id,
            share_type="link",
            share_token=secrets.token_urlsafe(48),
            permissions=permissions,
            expires_at=expires_at,
            created_by_id=created_by_id,
        )

    @property
    def is_valid(self) -> bool:
        """Prüft, ob die Freigabe noch gültig ist."""
        if self.expires_at is None:
            return True
        return datetime.now(UTC) < self.expires_at

    @property
    def can_write(self) -> bool:
        """Prüft, ob Schreibzugriff erlaubt ist."""
        return self.permissions == "write" and self.is_valid
