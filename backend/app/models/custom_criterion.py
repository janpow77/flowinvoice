"""
CustomCriterion Model

Model für benutzerdefinierte Prüfkriterien.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import CriterionLogicType


class CustomCriterion(Base):
    """
    Benutzerdefiniertes Prüfkriterium.

    Ermöglicht die Definition eigener Validierungsregeln für Dokumente.

    Beispiele:
    - Maximalbetrag pro Rechnung
    - Pflichtfelder für bestimmte Lieferanten
    - Zeitbasierte Regeln (z.B. keine Rechnungen vor Projektstart)
    """

    __tablename__ = "custom_criteria"

    # Primary Key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Zuordnung zu Projekt (optional - wenn None, gilt global)
    project_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Regelwerk-Zuordnung (optional)
    ruleset_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Name und Beschreibung
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Fehlercode (für Solution Files)
    error_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Schweregrad
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM")

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Logik-Typ
    logic_type: Mapped[str] = mapped_column(
        String(30),
        default=CriterionLogicType.COMPARISON.value,
    )

    # Regelkonfiguration als JSON
    # Struktur hängt vom logic_type ab
    rule_config: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Fehlermeldung (mit Platzhaltern)
    error_message_template: Mapped[str] = mapped_column(
        Text,
        default="Kriterium '{name}' nicht erfüllt.",
    )

    # Priorität (höher = wird zuerst geprüft)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Ersteller
    created_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    project = relationship("Project", backref="custom_criteria")

    def __repr__(self) -> str:
        return f"<CustomCriterion {self.name} ({self.error_code})>"

    def get_error_message(self, context: dict[str, Any] | None = None) -> str:
        """
        Generiert die Fehlermeldung mit Kontext.

        Args:
            context: Kontextwerte für Platzhalter

        Returns:
            Formatierte Fehlermeldung
        """
        template = self.error_message_template
        if context:
            try:
                return template.format(**context, name=self.name)
            except KeyError:
                pass
        return template.format(name=self.name)


# Vordefinierte Regel-Konfigurationen für verschiedene logic_types:

"""
SIMPLE_COMPARISON:
{
    "field": "gross_amount",
    "operator": "<=",      # ==, !=, <, <=, >, >=
    "value": 10000,
    "value_type": "number" # number, string, date
}

FIELD_REQUIRED:
{
    "field": "invoice_number",
    "condition": "not_empty"  # not_empty, not_null, matches_pattern
}

DATE_RANGE:
{
    "field": "invoice_date",
    "min_date": "project_start",  # Literal oder Referenz
    "max_date": "project_end",
    "include_boundaries": true
}

PATTERN_MATCH:
{
    "field": "supplier_vat_id",
    "pattern": "^DE[0-9]{9}$",
    "case_sensitive": false
}

FORMULA:
{
    "expression": "net_amount * (1 + vat_rate) == gross_amount",
    "tolerance": 0.01  # Erlaubte Abweichung
}

LOOKUP:
{
    "field": "supplier_name",
    "lookup_source": "blacklist",  # blacklist, whitelist, reference_table
    "lookup_values": ["Blocked GmbH", "Suspicious Inc"]
}

CONDITIONAL:
{
    "if": {
        "field": "gross_amount",
        "operator": ">",
        "value": 5000
    },
    "then": {
        "field": "supplier_vat_id",
        "condition": "not_empty"
    }
}

AGGREGATE:
{
    "aggregate_type": "sum",  # sum, count, avg, max, min
    "field": "gross_amount",
    "group_by": "supplier_name",
    "max_value": 50000,
    "time_window_days": 30
}
"""
