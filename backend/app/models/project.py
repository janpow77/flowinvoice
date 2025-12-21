# Pfad: /backend/app/models/project.py
"""
FlowAudit Project Model

Vorhaben/Projekt mit Begünstigtem und Durchführungsort.
"""

import secrets
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.user import User
    from app.models.batch_job import BatchJob


class Project(Base):
    """
    Vorhaben/Projekt für Rechnungsprüfung.

    Enthält:
    - Begünstigten (beneficiary) mit Adresse und Aliases
    - Projekt-Details mit Durchführungsort (implementation)
    - Zeitraum und Budget
    - Besitzer und Nutzer-Zuweisungen
    """

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    # Ruleset-Hinweis
    ruleset_id_hint: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ui_language_hint: Mapped[str] = mapped_column(String(5), default="de")

    # Begünstigter (JSON mit name, street, zip, city, country, vat_id, tax_number, aliases)
    beneficiary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Projekt-Details (JSON mit project_title, implementation, budget, period, etc.)
    project: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    # Besitzer (Admin, der das Projekt erstellt hat)
    owner_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    owner: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[owner_id],
    )

    # Nutzer, die diesem Projekt zugewiesen sind (Schüler)
    assigned_users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="assigned_project",
        foreign_keys="User.assigned_project_id",
    )

    # Externe Freigabe
    is_shared_externally: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    share_token: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
    )

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="project", cascade="all, delete-orphan"
    )
    batch_jobs: Mapped[list["BatchJob"]] = relationship(
        "BatchJob", back_populates="project", cascade="all, delete-orphan"
    )

    def generate_share_token(self) -> str:
        """Generiert ein neues Share-Token für externe Freigabe."""
        self.share_token = secrets.token_urlsafe(48)
        self.is_shared_externally = True
        return self.share_token

    def revoke_share_token(self) -> None:
        """Widerruft das Share-Token."""
        self.share_token = None
        self.is_shared_externally = False

    def __repr__(self) -> str:
        """String-Repräsentation."""
        title = self.project.get("project_title", "Unbenannt")
        return f"<Project {title[:30]}>"

    @property
    def project_title(self) -> str:
        """Projekt-Titel."""
        title: str = self.project.get("project_title", "")
        return title

    @property
    def file_reference(self) -> str | None:
        """Aktenzeichen."""
        return self.project.get("file_reference")

    @property
    def beneficiary_name(self) -> str:
        """Name des Begünstigten."""
        name: str = self.beneficiary.get("name", "")
        return name

    @property
    def beneficiary_aliases(self) -> list[str]:
        """Alias-Namen des Begünstigten."""
        aliases: list[str] = self.beneficiary.get("aliases", [])
        return aliases

    @property
    def implementation_location(self) -> dict[str, Any] | None:
        """Durchführungsort."""
        return self.project.get("implementation")

    @property
    def project_period(self) -> dict[str, Any] | None:
        """Projektzeitraum (Bewilligungszeitraum)."""
        return self.project.get("project_period")

    @property
    def execution_period(self) -> dict[str, Any] | None:
        """
        Durchführungszeitraum für Leistungsprüfung.

        Falls nicht explizit gesetzt, wird project_period verwendet.
        """
        return self.project.get("execution_period") or self.project.get("project_period")

    @property
    def project_description(self) -> str | None:
        """Projektbeschreibung für semantische Prüfung."""
        return self.project.get("project_description")

    @property
    def beneficiary_vat_id(self) -> str | None:
        """USt-IdNr. des Begünstigten für Selbstrechnungs-Prüfung."""
        return self.beneficiary.get("vat_id")

    @property
    def max_funding_amount(self) -> dict[str, Any] | None:
        """Maximale Fördersumme."""
        return self.project.get("max_funding_amount")

    @property
    def funding_rate_percent(self) -> float | None:
        """Fördersatz in Prozent."""
        return self.project.get("funding_rate_percent")

    def get_beneficiary_full_address(self) -> str:
        """
        Gibt vollständige Adresse des Begünstigten zurück.

        Returns:
            Formatierte Adresse.
        """
        b = self.beneficiary
        parts = [
            b.get("name", ""),
            b.get("street", ""),
            f"{b.get('zip', '')} {b.get('city', '')}".strip(),
            b.get("country", ""),
        ]
        return ", ".join(filter(None, parts))

    def get_implementation_full_address(self) -> str | None:
        """
        Gibt vollständige Adresse des Durchführungsorts zurück.

        Returns:
            Formatierte Adresse oder None.
        """
        impl = self.implementation_location
        if not impl:
            return None

        parts = [
            impl.get("location_name", ""),
            impl.get("street", ""),
            f"{impl.get('zip', '')} {impl.get('city', '')}".strip(),
            impl.get("country", ""),
        ]
        return ", ".join(filter(None, parts))
