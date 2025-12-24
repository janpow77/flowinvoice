# Pfad: /backend/app/models/ruleset_checker.py
"""
FlowAudit Ruleset Checker Settings Model

Konfiguration der Prüfmodule (Risk, Semantic, Economic) pro Regelwerk.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RulesetCheckerSettings(Base):
    """
    Prüfmodul-Konfiguration für ein Regelwerk.

    Jedes Regelwerk kann eigene Einstellungen für:
    - Risk Checker (Betrugsrisiken)
    - Semantic Checker (Projektrelevanz)
    - Economic Checker (Wirtschaftlichkeit)
    """

    __tablename__ = "ruleset_checker_settings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    # Referenz zum Regelwerk (ruleset_id, nicht die UUID)
    ruleset_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )

    # Risk Checker Konfiguration
    risk_checker: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "enabled": True,
            "severity_threshold": "MEDIUM",
            "check_self_invoice": True,
            "check_duplicate_invoice": True,
            "check_round_amounts": True,
            "check_weekend_dates": True,
            "round_amount_threshold": 1000,
        }
    )

    # Semantic Checker Konfiguration
    semantic_checker: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "enabled": True,
            "severity_threshold": "MEDIUM",
            "check_project_relevance": True,
            "check_description_quality": True,
            "min_relevance_score": 0.6,
            "use_rag_context": True,
        }
    )

    # Economic Checker Konfiguration
    economic_checker: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "enabled": True,
            "severity_threshold": "LOW",
            "check_budget_limits": True,
            "check_unit_prices": True,
            "check_funding_rate": True,
            "max_deviation_percent": 20,
        }
    )

    # Legal Checker Konfiguration (Legal Retrieval / Normenhierarchie)
    legal_checker: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "enabled": False,
            "funding_period": "2021-2027",
            "max_results": 5,
            "min_relevance_score": 0.6,
            "use_hierarchy_weighting": True,
            "include_definitions": True,
        }
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
        return f"<RulesetCheckerSettings {self.ruleset_id}>"

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "ruleset_id": self.ruleset_id,
            "risk_checker": self.risk_checker,
            "semantic_checker": self.semantic_checker,
            "economic_checker": self.economic_checker,
            "legal_checker": self.legal_checker,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
