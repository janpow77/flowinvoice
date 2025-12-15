# Pfad: /backend/app/models/ruleset.py
"""
FlowAudit Ruleset Model

Steuerliche Regelwerke (DE_USTG, EU_VAT, UK_VAT).
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import ARRAY, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    pass


class Ruleset(Base):
    """
    Steuerliches Regelwerk mit Features.

    Jedes Ruleset ist versioniert und immutable.
    Änderungen erzeugen neue Versionen.
    """

    __tablename__ = "rulesets"
    __table_args__ = (UniqueConstraint("ruleset_id", "version", name="uq_ruleset_version"),)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    ruleset_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(10), nullable=False)
    title_de: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[str] = mapped_column(String(255), nullable=False)

    # JSON-Felder
    legal_references: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    features: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    special_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Spracheinstellungen
    default_language: Mapped[str] = mapped_column(String(5), default="de")
    supported_ui_languages: Mapped[list[str]] = mapped_column(
        ARRAY(String(5)), default=["de", "en"]
    )
    currency_default: Mapped[str] = mapped_column(String(3), default="EUR")

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<Ruleset {self.ruleset_id} v{self.version}>"

    def get_feature_by_id(self, feature_id: str) -> dict | None:
        """
        Findet ein Feature nach ID.

        Args:
            feature_id: Feature-ID.

        Returns:
            Feature-Dict oder None.
        """
        for feature in self.features:
            if feature.get("feature_id") == feature_id:
                return feature
        return None

    def get_required_features(self) -> list[dict]:
        """
        Gibt alle Pflichtfeatures zurück.

        Returns:
            Liste der Pflichtfeatures.
        """
        return [
            f for f in self.features
            if f.get("required_level") == "REQUIRED"
        ]
