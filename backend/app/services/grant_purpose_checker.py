# Pfad: /backend/app/services/grant_purpose_checker.py
"""
Grant Purpose Checker Service (Zuwendungszweckprüfung)

Prüft den sachlichen, zeitlichen, organisatorischen und wirtschaftlichen
Zusammenhang einer Rechnung mit dem Förderzweck.
"""

from datetime import datetime

from app.models.enums import (
    DimensionResult,
    GrantPurposeDimension,
    UnclearReason,
)
from app.schemas.grant_purpose import (
    NEGATIVE_INDICATORS,
    DimensionAssessment,
    GrantPurposeAuditRequest,
    GrantPurposeAuditResult,
    NegativeIndicator,
)


class GrantPurposeChecker:
    """Prüft den Zuwendungszweck einer Rechnung."""

    def __init__(self) -> None:
        """Initialisiert den Grant Purpose Checker."""
        self.version = "1.0.0"

    def check(self, request: GrantPurposeAuditRequest) -> GrantPurposeAuditResult:
        """
        Führt vollständige Zuwendungszweckprüfung durch.

        Args:
            request: Prüfungsanfrage mit Rechnungs- und Projektdaten

        Returns:
            Strukturiertes Prüfergebnis mit Einzelbewertungen
        """
        negative_indicators: list[NegativeIndicator] = []

        # 1. Sachlicher Zusammenhang prüfen
        subject_assessment, subject_indicators = self._check_subject_relation(request)
        negative_indicators.extend(subject_indicators)

        # 2. Zeitlicher Zusammenhang prüfen
        temporal_assessment, temporal_indicators = self._check_temporal_relation(request)
        negative_indicators.extend(temporal_indicators)

        # 3. Organisatorischer Zusammenhang prüfen
        org_assessment, org_indicators = self._check_organizational_relation(request)
        negative_indicators.extend(org_indicators)

        # 4. Wirtschaftliche Plausibilität prüfen
        econ_assessment, econ_indicators = self._check_economic_plausibility(request)
        negative_indicators.extend(econ_indicators)

        # Gesamtergebnis ableiten
        result = GrantPurposeAuditResult(
            subject_relation=subject_assessment,
            temporal_relation=temporal_assessment,
            organizational_relation=org_assessment,
            economic_plausibility=econ_assessment,
            overall_result=DimensionResult.PASS,  # Wird überschrieben
            overall_reasoning="",
            negative_indicators=negative_indicators,
            audit_timestamp=datetime.utcnow().isoformat() + "Z",
            audit_version=self.version,
        )

        # Gesamtergebnis algorithmisch ableiten
        result.overall_result = result.derive_overall_result()
        result.overall_reasoning = self._derive_overall_reasoning(result)

        return result

    def _check_subject_relation(
        self, request: GrantPurposeAuditRequest
    ) -> tuple[DimensionAssessment, list[NegativeIndicator]]:
        """Prüft sachlichen Zusammenhang."""
        indicators: list[NegativeIndicator] = []
        evidence: list[str] = []

        description = request.invoice_description.lower()
        project_name = (request.project_name or "").lower()
        project_description = (request.project_description or "").lower()

        # Prüfe auf Projektbezug in Leistungsbeschreibung
        has_project_reference = False
        if project_name and project_name in description:
            has_project_reference = True
            evidence.append(f"Projektname '{request.project_name}' in Beschreibung gefunden")

        # Prüfe auf generische Leistungen ohne spezifischen Bezug
        generic_terms = [
            "diverses", "sonstiges", "pauschale", "allgemein",
            "verschiedene leistungen", "nach aufwand"
        ]
        has_generic_terms = any(term in description for term in generic_terms)
        if has_generic_terms:
            indicators.append(NEGATIVE_INDICATORS["GENERIC_SERVICE"])
            evidence.append("Generische Leistungsbeschreibung erkannt")

        # Bewertung ableiten
        if has_project_reference and not has_generic_terms:
            result = DimensionResult.PASS
            reasoning = "Leistungsbeschreibung weist klaren Projektbezug auf"
        elif not has_project_reference and has_generic_terms:
            result = DimensionResult.FAIL
            reasoning = "Kein Projektbezug erkennbar, generische Beschreibung"
            indicators.append(NEGATIVE_INDICATORS["NO_PROJECT_REFERENCE"])
        elif not project_name and not project_description:
            result = DimensionResult.UNCLEAR
            reasoning = "Projektkontext nicht verfügbar, Prüfung nicht möglich"
        else:
            result = DimensionResult.UNCLEAR
            reasoning = "Projektbezug nicht eindeutig erkennbar"

        assessment = DimensionAssessment(
            dimension=GrantPurposeDimension.SUBJECT_RELATION,
            result=result,
            confidence=0.8 if result == DimensionResult.PASS else 0.6,
            reasoning=reasoning,
            evidence=evidence,
            unclear_reason=UnclearReason.INSUFFICIENT_CONTEXT if result == DimensionResult.UNCLEAR else None,
            required_clarification="Projektbeschreibung oder -ziele zur Prüfung benötigt" if result == DimensionResult.UNCLEAR else None,
        )

        return assessment, indicators

    def _check_temporal_relation(
        self, request: GrantPurposeAuditRequest
    ) -> tuple[DimensionAssessment, list[NegativeIndicator]]:
        """Prüft zeitlichen Zusammenhang."""
        indicators: list[NegativeIndicator] = []
        evidence: list[str] = []

        # Wenn kein Projektzeitraum definiert
        if not request.project_start or not request.project_end:
            return DimensionAssessment(
                dimension=GrantPurposeDimension.TEMPORAL_RELATION,
                result=DimensionResult.UNCLEAR,
                confidence=0.5,
                reasoning="Projektzeitraum nicht definiert",
                evidence=["Projekt-Start/Ende fehlt"],
                unclear_reason=UnclearReason.MISSING_INFORMATION,
                required_clarification="Projektzeitraum (Start- und Enddatum) benötigt",
            ), indicators

        # Prüfe Leistungszeitraum
        service_start = request.service_period_start or request.invoice_date
        service_end = request.service_period_end or request.invoice_date

        evidence.append(f"Leistungszeitraum: {service_start} - {service_end}")
        evidence.append(f"Projektzeitraum: {request.project_start} - {request.project_end}")

        # Fehlender Leistungszeitraum
        if not request.service_period_start and not request.service_period_end:
            indicators.append(NEGATIVE_INDICATORS["MISSING_SERVICE_PERIOD"])
            evidence.append("Leistungszeitraum auf Rechnung fehlt")

        # Prüfe ob Leistungszeitraum innerhalb Projektzeitraum
        if service_start < request.project_start or service_end > request.project_end:
            indicators.append(NEGATIVE_INDICATORS["OUTSIDE_PROJECT_PERIOD"])
            return DimensionAssessment(
                dimension=GrantPurposeDimension.TEMPORAL_RELATION,
                result=DimensionResult.FAIL,
                confidence=0.95,
                reasoning="Leistungszeitraum liegt (teilweise) außerhalb des Projektzeitraums",
                evidence=evidence,
            ), indicators

        # Leistungszeitraum innerhalb Projektzeitraum
        return DimensionAssessment(
            dimension=GrantPurposeDimension.TEMPORAL_RELATION,
            result=DimensionResult.PASS,
            confidence=0.95,
            reasoning="Leistungszeitraum liegt vollständig im Projektzeitraum",
            evidence=evidence,
        ), indicators

    def _check_organizational_relation(
        self, request: GrantPurposeAuditRequest
    ) -> tuple[DimensionAssessment, list[NegativeIndicator]]:
        """Prüft organisatorischen Zusammenhang (Empfänger = Begünstigter)."""
        indicators: list[NegativeIndicator] = []
        evidence: list[str] = []

        # Wenn kein Begünstigter definiert
        if not request.beneficiary_name:
            return DimensionAssessment(
                dimension=GrantPurposeDimension.ORGANIZATIONAL_RELATION,
                result=DimensionResult.UNCLEAR,
                confidence=0.5,
                reasoning="Begünstigtendaten nicht verfügbar",
                evidence=["Begünstigter nicht definiert"],
                unclear_reason=UnclearReason.MISSING_INFORMATION,
                required_clarification="Begünstigtendaten (Name, Adresse) benötigt",
            ), indicators

        recipient = request.invoice_recipient.lower().strip()
        beneficiary = request.beneficiary_name.lower().strip()
        aliases = [a.lower().strip() for a in request.beneficiary_aliases]

        evidence.append(f"Rechnungsempfänger: {request.invoice_recipient}")
        evidence.append(f"Begünstigter: {request.beneficiary_name}")

        # Exakter Match
        if recipient == beneficiary:
            return DimensionAssessment(
                dimension=GrantPurposeDimension.ORGANIZATIONAL_RELATION,
                result=DimensionResult.PASS,
                confidence=1.0,
                reasoning="Rechnungsempfänger entspricht exakt dem Begünstigten",
                evidence=evidence,
            ), indicators

        # Alias-Match
        if recipient in aliases:
            evidence.append(f"Alias-Match: {recipient}")
            return DimensionAssessment(
                dimension=GrantPurposeDimension.ORGANIZATIONAL_RELATION,
                result=DimensionResult.PASS,
                confidence=0.9,
                reasoning="Rechnungsempfänger entspricht bekanntem Alias des Begünstigten",
                evidence=evidence,
            ), indicators

        # Fuzzy-Match (enthält Begünstigten-Namen)
        if beneficiary in recipient or recipient in beneficiary:
            return DimensionAssessment(
                dimension=GrantPurposeDimension.ORGANIZATIONAL_RELATION,
                result=DimensionResult.UNCLEAR,
                confidence=0.7,
                reasoning="Teilweise Übereinstimmung zwischen Empfänger und Begünstigtem",
                evidence=evidence,
                unclear_reason=UnclearReason.AMBIGUOUS_DATA,
                required_clarification="Manuelle Prüfung der Namensübereinstimmung erforderlich",
            ), indicators

        # Keine Übereinstimmung
        indicators.append(NEGATIVE_INDICATORS["RECIPIENT_MISMATCH"])
        return DimensionAssessment(
            dimension=GrantPurposeDimension.ORGANIZATIONAL_RELATION,
            result=DimensionResult.FAIL,
            confidence=0.9,
            reasoning="Rechnungsempfänger entspricht nicht dem Begünstigten",
            evidence=evidence,
        ), indicators

    def _check_economic_plausibility(
        self, request: GrantPurposeAuditRequest
    ) -> tuple[DimensionAssessment, list[NegativeIndicator]]:
        """Prüft wirtschaftliche Plausibilität."""
        indicators: list[NegativeIndicator] = []
        evidence: list[str] = []

        amount = request.net_amount
        evidence.append(f"Nettobetrag: {amount:.2f} EUR")

        # Prüfe auf ungewöhnlich hohe Beträge (didaktischer Hinweis)
        # Schwellenwert: 50.000 EUR für Einzelrechnung
        if amount > 50000:
            indicators.append(NEGATIVE_INDICATORS["UNUSUALLY_HIGH_AMOUNT"])
            evidence.append("Betrag überschreitet Schwellenwert von 50.000 EUR")

        # Prüfe auf runde Beträge (möglicher Pauschalpreis ohne Kalkulation)
        if amount > 1000 and amount == int(amount) and amount % 100 == 0:
            evidence.append("Runder Pauschalbetrag erkannt")

        # Ohne weitere Vergleichsdaten nur eingeschränkte Prüfung möglich
        if amount <= 0:
            return DimensionAssessment(
                dimension=GrantPurposeDimension.ECONOMIC_PLAUSIBILITY,
                result=DimensionResult.FAIL,
                confidence=1.0,
                reasoning="Ungültiger Betrag (≤ 0)",
                evidence=evidence,
            ), indicators

        if indicators:
            return DimensionAssessment(
                dimension=GrantPurposeDimension.ECONOMIC_PLAUSIBILITY,
                result=DimensionResult.UNCLEAR,
                confidence=0.6,
                reasoning="Wirtschaftlichkeit aufgrund hoher Beträge prüfenswert",
                evidence=evidence,
                unclear_reason=UnclearReason.INSUFFICIENT_CONTEXT,
                required_clarification="Vergleichsangebote oder Marktpreise zur Validierung",
            ), indicators

        return DimensionAssessment(
            dimension=GrantPurposeDimension.ECONOMIC_PLAUSIBILITY,
            result=DimensionResult.PASS,
            confidence=0.7,
            reasoning="Betrag im erwartbaren Rahmen",
            evidence=evidence,
        ), indicators

    def _derive_overall_reasoning(self, result: GrantPurposeAuditResult) -> str:
        """Leitet zusammenfassende Begründung ab."""
        results = {
            "Sachlich": result.subject_relation.result,
            "Zeitlich": result.temporal_relation.result,
            "Organisatorisch": result.organizational_relation.result,
            "Wirtschaftlich": result.economic_plausibility.result,
        }

        passed = [k for k, v in results.items() if v == DimensionResult.PASS]
        failed = [k for k, v in results.items() if v == DimensionResult.FAIL]
        unclear = [k for k, v in results.items() if v == DimensionResult.UNCLEAR]

        if result.overall_result == DimensionResult.PASS:
            return f"Alle Prüfdimensionen erfüllt: {', '.join(passed)}"
        elif result.overall_result == DimensionResult.FAIL:
            return f"Prüfung nicht bestanden. Probleme bei: {', '.join(failed)}"
        else:
            parts = []
            if failed:
                parts.append(f"Nicht erfüllt: {', '.join(failed)}")
            if unclear:
                parts.append(f"Unklar: {', '.join(unclear)}")
            return "Manuelle Prüfung erforderlich. " + "; ".join(parts)


# Singleton-Instanz
grant_purpose_checker = GrantPurposeChecker()
