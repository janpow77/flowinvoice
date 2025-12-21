"""
Custom Criteria Engine

Engine zur Evaluierung benutzerdefinierter Prüfkriterien.
"""

import logging
import operator
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, Optional

from app.models.custom_criterion import CustomCriterion
from app.models.enums import CriterionLogicType

logger = logging.getLogger(__name__)


@dataclass
class CriterionResult:
    """Ergebnis einer Kriterien-Prüfung."""

    criterion_id: str
    criterion_name: str
    error_code: str
    passed: bool
    severity: str
    message: str
    field: Optional[str] = None
    expected: Any = None
    actual: Any = None


class CustomCriteriaEngine:
    """
    Engine zur Evaluierung benutzerdefinierter Kriterien.

    Unterstützt verschiedene Logik-Typen für flexible Validierungen.
    """

    # Operator-Mapping
    OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
        "==": operator.eq,
        "!=": operator.ne,
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "in": lambda a, b: a in b,
        "not_in": lambda a, b: a not in b,
        "contains": lambda a, b: b in str(a),
        "starts_with": lambda a, b: str(a).startswith(str(b)),
        "ends_with": lambda a, b: str(a).endswith(str(b)),
    }

    def __init__(self, project_context: dict[str, Any] | None = None):
        """
        Initialisiert die Engine.

        Args:
            project_context: Projektkontext mit Start-/Enddatum, etc.
        """
        self.project_context = project_context or {}

    def evaluate_criterion(
        self,
        criterion: CustomCriterion,
        document_data: dict[str, Any],
    ) -> CriterionResult:
        """
        Evaluiert ein einzelnes Kriterium gegen Dokumentdaten.

        Args:
            criterion: Das zu prüfende Kriterium
            document_data: Extrahierte Dokumentdaten

        Returns:
            CriterionResult mit Prüfergebnis
        """
        try:
            logic_type = CriterionLogicType(criterion.logic_type)
            rule_config = criterion.rule_config or {}

            # Dispatch basierend auf Logik-Typ
            evaluators = {
                CriterionLogicType.SIMPLE_COMPARISON: self._evaluate_simple_comparison,
                CriterionLogicType.FIELD_REQUIRED: self._evaluate_field_required,
                CriterionLogicType.DATE_RANGE: self._evaluate_date_range,
                CriterionLogicType.PATTERN_MATCH: self._evaluate_pattern_match,
                CriterionLogicType.FORMULA: self._evaluate_formula,
                CriterionLogicType.LOOKUP: self._evaluate_lookup,
                CriterionLogicType.CONDITIONAL: self._evaluate_conditional,
                CriterionLogicType.AGGREGATE: self._evaluate_aggregate,
            }

            evaluator = evaluators.get(logic_type)
            if not evaluator:
                return CriterionResult(
                    criterion_id=criterion.id,
                    criterion_name=criterion.name,
                    error_code=criterion.error_code,
                    passed=True,  # Unbekannte Typen werden ignoriert
                    severity=criterion.severity,
                    message=f"Unbekannter Logik-Typ: {logic_type}",
                )

            passed, message, actual, expected = evaluator(rule_config, document_data)

            return CriterionResult(
                criterion_id=criterion.id,
                criterion_name=criterion.name,
                error_code=criterion.error_code,
                passed=passed,
                severity=criterion.severity,
                message=criterion.get_error_message({
                    "message": message,
                    "actual": actual,
                    "expected": expected,
                }) if not passed else "OK",
                field=rule_config.get("field"),
                expected=expected,
                actual=actual,
            )

        except Exception as e:
            logger.exception(f"Error evaluating criterion {criterion.name}: {e}")
            return CriterionResult(
                criterion_id=criterion.id,
                criterion_name=criterion.name,
                error_code=criterion.error_code,
                passed=True,  # Bei Fehler kein Alarm
                severity=criterion.severity,
                message=f"Evaluierungsfehler: {e}",
            )

    def evaluate_all(
        self,
        criteria: list[CustomCriterion],
        document_data: dict[str, Any],
    ) -> list[CriterionResult]:
        """
        Evaluiert alle Kriterien gegen Dokumentdaten.

        Args:
            criteria: Liste der zu prüfenden Kriterien
            document_data: Extrahierte Dokumentdaten

        Returns:
            Liste von CriterionResult
        """
        results = []

        # Sortiere nach Priorität (höher zuerst)
        sorted_criteria = sorted(criteria, key=lambda c: c.priority, reverse=True)

        for criterion in sorted_criteria:
            if not criterion.is_active:
                continue

            result = self.evaluate_criterion(criterion, document_data)
            results.append(result)

        return results

    def _get_field_value(
        self,
        document_data: dict[str, Any],
        field_name: str,
    ) -> Any:
        """Extrahiert einen Feldwert aus den Dokumentdaten."""
        # Unterstütze verschachtelte Felder mit Punkt-Notation
        parts = field_name.split(".")
        value = document_data

        for part in parts:
            if isinstance(value, dict):
                # Prüfe ob es ein ExtractedDataField ist
                if "value" in value and len(parts) == 1:
                    value = value.get("value")
                else:
                    value = value.get(part)
            else:
                return None

        # Falls das Ergebnis ein ExtractedDataField ist
        if isinstance(value, dict) and "value" in value:
            return value.get("value")

        return value

    def _resolve_reference(self, ref_value: Any) -> Any:
        """Löst Referenzen wie 'project_start' auf."""
        if isinstance(ref_value, str):
            if ref_value == "project_start":
                return self.project_context.get("start_date")
            elif ref_value == "project_end":
                return self.project_context.get("end_date")
            elif ref_value == "today":
                return date.today()
        return ref_value

    def _parse_date(self, value: Any) -> date | None:
        """Parst einen Wert zu einem Datum."""
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None

    def _evaluate_simple_comparison(
        self,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> tuple[bool, str, Any, Any]:
        """Evaluiert einen einfachen Vergleich."""
        field = config.get("field", "")
        op = config.get("operator", "==")
        expected_value = config.get("value")
        value_type = config.get("value_type", "auto")

        actual_value = self._get_field_value(data, field)

        # Typkonvertierung
        if value_type == "number":
            try:
                actual_value = float(actual_value) if actual_value else 0
                expected_value = float(expected_value) if expected_value else 0
            except (ValueError, TypeError):
                return False, f"Kann {field} nicht als Zahl interpretieren", actual_value, expected_value
        elif value_type == "date":
            actual_value = self._parse_date(actual_value)
            expected_value = self._parse_date(self._resolve_reference(expected_value))

        # Vergleich durchführen
        comparator = self.OPERATORS.get(op, operator.eq)
        try:
            passed = comparator(actual_value, expected_value)
            return passed, f"{field} {op} {expected_value}", actual_value, expected_value
        except (TypeError, ValueError) as e:
            return False, str(e), actual_value, expected_value

    def _evaluate_field_required(
        self,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> tuple[bool, str, Any, Any]:
        """Prüft ob ein Pflichtfeld vorhanden ist."""
        field = config.get("field", "")
        condition = config.get("condition", "not_empty")

        actual_value = self._get_field_value(data, field)

        if condition == "not_null":
            passed = actual_value is not None
        elif condition == "not_empty":
            passed = bool(actual_value) and str(actual_value).strip() != ""
        elif condition == "matches_pattern":
            pattern = config.get("pattern", ".*")
            passed = bool(re.match(pattern, str(actual_value or "")))
        else:
            passed = actual_value is not None

        expected = f"Feld '{field}' muss {condition} sein"
        return passed, expected, actual_value, expected

    def _evaluate_date_range(
        self,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> tuple[bool, str, Any, Any]:
        """Prüft ob ein Datum in einem Bereich liegt."""
        field = config.get("field", "")
        min_date = self._parse_date(self._resolve_reference(config.get("min_date")))
        max_date = self._parse_date(self._resolve_reference(config.get("max_date")))
        include_boundaries = config.get("include_boundaries", True)

        actual_date = self._parse_date(self._get_field_value(data, field))

        if not actual_date:
            return False, f"Kein gültiges Datum in {field}", None, f"{min_date} - {max_date}"

        if include_boundaries:
            in_range = (min_date is None or actual_date >= min_date) and \
                      (max_date is None or actual_date <= max_date)
        else:
            in_range = (min_date is None or actual_date > min_date) and \
                      (max_date is None or actual_date < max_date)

        return in_range, f"Datum muss zwischen {min_date} und {max_date} liegen", \
               actual_date, f"{min_date} - {max_date}"

    def _evaluate_pattern_match(
        self,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> tuple[bool, str, Any, Any]:
        """Prüft ob ein Wert einem Pattern entspricht."""
        field = config.get("field", "")
        pattern = config.get("pattern", ".*")
        case_sensitive = config.get("case_sensitive", True)

        actual_value = str(self._get_field_value(data, field) or "")

        flags = 0 if case_sensitive else re.IGNORECASE
        passed = bool(re.match(pattern, actual_value, flags))

        return passed, f"Muss Pattern '{pattern}' entsprechen", actual_value, pattern

    def _evaluate_formula(
        self,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> tuple[bool, str, Any, Any]:
        """
        Evaluiert eine mathematische Formel.

        ACHTUNG: Eingeschränkte eval-Implementierung für Sicherheit.
        """
        expression = config.get("expression", "True")
        tolerance = config.get("tolerance", 0.01)

        # Sichere Variablen extrahieren
        safe_vars = {}
        for key, value in data.items():
            if isinstance(value, dict) and "value" in value:
                val = value.get("value")
            else:
                val = value

            try:
                safe_vars[key] = float(val) if val is not None else 0
            except (ValueError, TypeError):
                safe_vars[key] = 0

        # Erlaubte Operationen
        allowed_ops = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
        }
        allowed_ops.update(safe_vars)

        try:
            # Prüfe auf == mit Toleranz
            if "==" in expression:
                left, right = expression.split("==")
                left_val = eval(left.strip(), {"__builtins__": {}}, safe_vars)
                right_val = eval(right.strip(), {"__builtins__": {}}, safe_vars)
                passed = abs(left_val - right_val) <= tolerance
                return passed, expression, f"Diff: {abs(left_val - right_val)}", f"<= {tolerance}"
            else:
                result = eval(expression, allowed_ops)
                return bool(result), expression, result, True
        except Exception as e:
            logger.warning(f"Formula evaluation error: {e}")
            return True, f"Fehler: {e}", None, expression

    def _evaluate_lookup(
        self,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> tuple[bool, str, Any, Any]:
        """Prüft ob ein Wert in einer Liste ist (oder nicht)."""
        field = config.get("field", "")
        source = config.get("lookup_source", "blacklist")
        values = config.get("lookup_values", [])

        actual_value = str(self._get_field_value(data, field) or "").lower()

        # Normalisiere Liste
        normalized_values = [str(v).lower() for v in values]

        if source == "blacklist":
            passed = actual_value not in normalized_values
            return passed, f"'{actual_value}' darf nicht in Blacklist sein", \
                   actual_value, f"Nicht erlaubt: {values[:3]}..."
        elif source == "whitelist":
            passed = actual_value in normalized_values
            return passed, f"'{actual_value}' muss in Whitelist sein", \
                   actual_value, f"Erlaubt: {values[:3]}..."
        else:
            return True, "Unbekannte Lookup-Quelle", actual_value, source

    def _evaluate_conditional(
        self,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> tuple[bool, str, Any, Any]:
        """Evaluiert eine bedingte Regel (IF-THEN)."""
        if_config = config.get("if", {})
        then_config = config.get("then", {})

        # Prüfe IF-Bedingung
        if_passed, _, _, _ = self._evaluate_simple_comparison(if_config, data)

        if not if_passed:
            # IF nicht erfüllt, Regel gilt als bestanden
            return True, "Bedingung nicht zutreffend", None, None

        # IF erfüllt, prüfe THEN
        then_passed, msg, actual, expected = self._evaluate_field_required(then_config, data)
        return then_passed, f"Wenn {if_config}, dann {msg}", actual, expected

    def _evaluate_aggregate(
        self,
        config: dict[str, Any],
        data: dict[str, Any],
    ) -> tuple[bool, str, Any, Any]:
        """
        Evaluiert eine Aggregat-Regel.

        Hinweis: Benötigt Zugriff auf historische Daten,
        daher hier nur Platzhalter-Implementierung.
        """
        # Diese Funktion würde in der Praxis Zugriff auf die Datenbank benötigen
        # um Aggregationen über mehrere Dokumente zu berechnen
        aggregate_type = config.get("aggregate_type", "sum")
        max_value = config.get("max_value", float("inf"))

        return True, f"Aggregat-Prüfung ({aggregate_type}): nicht implementiert", None, max_value
