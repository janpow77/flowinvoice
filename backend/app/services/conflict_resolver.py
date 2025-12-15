# Pfad: /backend/app/services/conflict_resolver.py
"""
Conflict Resolver Service

Auflösung von Konflikten zwischen regelbasierten Prüfungen (RULE),
KI-Analysen (LLM) und manuellen Korrekturen (USER).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.enums import ConflictStatus, TruthSource


@dataclass
class SourceValue:
    """Wert aus einer bestimmten Quelle."""

    source: TruthSource
    value: Any
    confidence: float = 1.0
    timestamp: str | None = None
    reasoning: str | None = None


@dataclass
class ResolvedValue:
    """Aufgelöster Wert nach Konfliktauflösung."""

    final_value: Any
    source: TruthSource
    conflict_status: ConflictStatus
    all_values: dict[TruthSource, SourceValue]
    resolution_reasoning: str
    resolution_timestamp: str


class ConflictResolver:
    """
    Löst Konflikte zwischen verschiedenen Prüfquellen auf.

    Prioritätslogik:
    1. USER (manuell) - höchste Priorität, übersteuert alles
    2. RULE (regelbasiert) - deterministisch, höher als KI
    3. LLM (KI-basiert) - niedrigste Priorität

    Bei Konflikten wird immer die höherpriore Quelle verwendet,
    der Konflikt aber dokumentiert.
    """

    PRIORITY_ORDER = [TruthSource.USER, TruthSource.RULE, TruthSource.LLM]

    def __init__(self) -> None:
        """Initialisiert den Conflict Resolver."""
        pass

    def resolve(
        self,
        rule_value: SourceValue | None = None,
        llm_value: SourceValue | None = None,
        user_value: SourceValue | None = None,
    ) -> ResolvedValue:
        """
        Löst Konflikt zwischen Quellen auf.

        Args:
            rule_value: Wert aus regelbasierter Prüfung
            llm_value: Wert aus KI-Analyse
            user_value: Manuell korrigierter Wert

        Returns:
            Aufgelöster Wert mit Konfliktdokumentation
        """
        values: dict[TruthSource, SourceValue] = {}

        if rule_value:
            values[TruthSource.RULE] = rule_value
        if llm_value:
            values[TruthSource.LLM] = llm_value
        if user_value:
            values[TruthSource.USER] = user_value

        if not values:
            raise ValueError("Mindestens ein Wert muss angegeben werden")

        # Konfliktstatus ermitteln
        conflict_status = self._detect_conflict(values)

        # Finalen Wert nach Priorität auswählen
        final_source, final_value, reasoning = self._resolve_by_priority(values)

        return ResolvedValue(
            final_value=final_value.value,
            source=final_source,
            conflict_status=conflict_status,
            all_values=values,
            resolution_reasoning=reasoning,
            resolution_timestamp=datetime.utcnow().isoformat() + "Z",
        )

    def _detect_conflict(
        self, values: dict[TruthSource, SourceValue]
    ) -> ConflictStatus:
        """Erkennt Konflikte zwischen den Quellen."""
        sources = list(values.keys())

        if len(sources) <= 1:
            return ConflictStatus.NO_CONFLICT

        # Alle Werte vergleichen
        unique_values = set()
        for sv in values.values():
            # Für Vergleich: Wert normalisieren
            normalized = self._normalize_value(sv.value)
            unique_values.add(normalized)

        # Keine Konflikte wenn alle Werte gleich
        if len(unique_values) == 1:
            return ConflictStatus.NO_CONFLICT

        # Spezifische Konflikte identifizieren
        has_rule = TruthSource.RULE in values
        has_llm = TruthSource.LLM in values
        has_user = TruthSource.USER in values

        if has_user:
            # User überschreibt etwas
            if has_rule and self._values_differ(
                values[TruthSource.USER], values[TruthSource.RULE]
            ):
                return ConflictStatus.CONFLICT_RULE_USER
            if has_llm and self._values_differ(
                values[TruthSource.USER], values[TruthSource.LLM]
            ):
                return ConflictStatus.CONFLICT_LLM_USER

        if has_rule and has_llm and self._values_differ(
            values[TruthSource.RULE], values[TruthSource.LLM]
        ):
            return ConflictStatus.CONFLICT_RULE_LLM

        return ConflictStatus.NO_CONFLICT

    def _resolve_by_priority(
        self, values: dict[TruthSource, SourceValue]
    ) -> tuple[TruthSource, SourceValue, str]:
        """Wählt Wert nach Priorität aus."""
        for source in self.PRIORITY_ORDER:
            if source in values:
                reasoning = self._build_reasoning(source, values)
                return source, values[source], reasoning

        # Sollte nie erreicht werden
        raise ValueError("Keine gültige Quelle gefunden")

    def _build_reasoning(
        self, selected_source: TruthSource, values: dict[TruthSource, SourceValue]
    ) -> str:
        """Erstellt Begründung für die Auflösung."""
        sources = list(values.keys())

        if len(sources) == 1:
            return f"Einzige verfügbare Quelle: {selected_source.value}"

        if selected_source == TruthSource.USER:
            return "Manuelle Korrektur übersteuert automatische Prüfungen"
        elif selected_source == TruthSource.RULE:
            if TruthSource.LLM in values:
                return "Regelbasierte Prüfung hat Vorrang vor KI-Analyse"
            return "Regelbasierte Prüfung verwendet"
        else:
            return "KI-Analyse verwendet (keine höherpriore Quelle verfügbar)"

    def _normalize_value(self, value: Any) -> str:
        """Normalisiert Wert für Vergleich."""
        if value is None:
            return "__NONE__"
        if isinstance(value, (list, dict)):
            return str(sorted(str(v) for v in (value if isinstance(value, list) else value.items())))
        return str(value).lower().strip()

    def _values_differ(self, sv1: SourceValue, sv2: SourceValue) -> bool:
        """Prüft ob zwei SourceValues unterschiedliche Werte haben."""
        return self._normalize_value(sv1.value) != self._normalize_value(sv2.value)

    def merge_results(
        self,
        rule_results: dict[str, Any],
        llm_results: dict[str, Any],
        user_overrides: dict[str, Any] | None = None,
    ) -> dict[str, ResolvedValue]:
        """
        Führt komplette Ergebnismengen zusammen.

        Args:
            rule_results: Alle regelbasierten Ergebnisse
            llm_results: Alle KI-Ergebnisse
            user_overrides: Manuelle Überschreibungen

        Returns:
            Dictionary mit aufgelösten Werten pro Feld
        """
        user_overrides = user_overrides or {}
        all_fields = set(rule_results.keys()) | set(llm_results.keys()) | set(user_overrides.keys())

        resolved = {}
        timestamp = datetime.utcnow().isoformat() + "Z"

        for field in all_fields:
            rule_val = None
            llm_val = None
            user_val = None

            if field in rule_results:
                rule_val = SourceValue(
                    source=TruthSource.RULE,
                    value=rule_results[field],
                    timestamp=timestamp,
                )

            if field in llm_results:
                llm_val = SourceValue(
                    source=TruthSource.LLM,
                    value=llm_results[field],
                    timestamp=timestamp,
                )

            if field in user_overrides:
                user_val = SourceValue(
                    source=TruthSource.USER,
                    value=user_overrides[field],
                    timestamp=timestamp,
                )

            resolved[field] = self.resolve(
                rule_value=rule_val,
                llm_value=llm_val,
                user_value=user_val,
            )

        return resolved


# Singleton-Instanz
conflict_resolver = ConflictResolver()
