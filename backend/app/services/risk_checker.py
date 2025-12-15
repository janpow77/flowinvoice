# Pfad: /backend/app/services/risk_checker.py
"""
Risk Checker Service

Prüft Rechnungen auf Risikoindikatoren.
Didaktische Hinweise für Seminarbetrieb - keine rechtliche Bewertung.
"""

import re
from datetime import datetime
from typing import Optional

from app.models.enums import RiskIndicator, Severity
from app.schemas.risk import (
    RiskAssessmentRequest,
    RiskAssessmentResult,
    RiskContext,
    RiskFinding,
)


class RiskChecker:
    """
    Prüft Rechnungen auf potenzielle Risikoindikatoren.

    Minimal-Risikokern (immer prüfen):
    - Ungewöhnlich hohe Einzelbeträge (> Median + 2σ)
    - Auffällige Lieferantenhäufung
    - Fehlende Leistungszeiträume
    - Runde Pauschalbeträge ohne Erläuterung
    - Leistungen außerhalb Projektzeitraum
    """

    # Schwellenwerte
    HIGH_AMOUNT_ABSOLUTE = 50000.0  # Absoluter Schwellenwert
    HIGH_AMOUNT_SIGMA = 2.0  # Anzahl Standardabweichungen
    VENDOR_CONCENTRATION_THRESHOLD = 0.3  # 30% aller Rechnungen
    ROUND_AMOUNT_THRESHOLD = 1000.0  # Ab diesem Betrag prüfen

    def __init__(self) -> None:
        """Initialisiert den Risk Checker."""
        self.version = "1.0.0"

    def assess(self, request: RiskAssessmentRequest) -> RiskAssessmentResult:
        """
        Führt Risikobewertung für eine Rechnung durch.

        Args:
            request: Rechnungsdaten und Kontext

        Returns:
            Risikobewertung mit Findings und Score
        """
        findings: list[RiskFinding] = []

        # 1. Hohe Beträge prüfen
        high_amount_finding = self._check_high_amount(request)
        if high_amount_finding:
            findings.append(high_amount_finding)

        # 2. Lieferantenhäufung prüfen
        vendor_finding = self._check_vendor_clustering(request)
        if vendor_finding:
            findings.append(vendor_finding)

        # 3. Fehlenden Leistungszeitraum prüfen
        period_finding = self._check_missing_period(request)
        if period_finding:
            findings.append(period_finding)

        # 4. Runde Beträge prüfen
        round_finding = self._check_round_amount(request)
        if round_finding:
            findings.append(round_finding)

        # 5. Zeitraum außerhalb Projekt prüfen
        outside_finding = self._check_outside_project_period(request)
        if outside_finding:
            findings.append(outside_finding)

        # 6. Projektbezug prüfen
        reference_finding = self._check_project_reference(request)
        if reference_finding:
            findings.append(reference_finding)

        # 7. Empfänger prüfen
        recipient_finding = self._check_recipient_mismatch(request)
        if recipient_finding:
            findings.append(recipient_finding)

        # Ergebnis zusammenstellen
        risk_score = self._calculate_risk_score(findings)
        highest_severity = self._get_highest_severity(findings)
        summary = self._build_summary(findings)

        return RiskAssessmentResult(
            findings=findings,
            risk_score=risk_score,
            highest_severity=highest_severity,
            summary=summary,
            assessment_timestamp=datetime.utcnow().isoformat() + "Z",
            assessment_version=self.version,
        )

    def _check_high_amount(
        self, request: RiskAssessmentRequest
    ) -> Optional[RiskFinding]:
        """Prüft auf ungewöhnlich hohe Beträge."""
        amount = request.net_amount
        context = request.context

        # Absoluter Schwellenwert
        if amount > self.HIGH_AMOUNT_ABSOLUTE:
            return RiskFinding(
                indicator=RiskIndicator.HIGH_AMOUNT,
                severity=Severity.MEDIUM,
                description=f"Ungewöhnlich hoher Einzelbetrag: {amount:.2f} EUR",
                evidence=f"Betrag überschreitet absoluten Schwellenwert von {self.HIGH_AMOUNT_ABSOLUTE:.2f} EUR",
                recommendation="Prüfung der Wirtschaftlichkeit und Vergleich mit Marktpreisen empfohlen",
            )

        # Relativer Schwellenwert (wenn Vergleichsdaten verfügbar)
        if context and context.median_amount and context.std_deviation:
            threshold = context.median_amount + (self.HIGH_AMOUNT_SIGMA * context.std_deviation)
            if amount > threshold:
                return RiskFinding(
                    indicator=RiskIndicator.HIGH_AMOUNT,
                    severity=Severity.MEDIUM,
                    description=f"Betrag weicht signifikant vom Median ab: {amount:.2f} EUR",
                    evidence=f"Median: {context.median_amount:.2f} EUR, Schwellenwert (Median + 2σ): {threshold:.2f} EUR",
                    recommendation="Statistische Auffälligkeit prüfen",
                )

        return None

    def _check_vendor_clustering(
        self, request: RiskAssessmentRequest
    ) -> Optional[RiskFinding]:
        """Prüft auf auffällige Lieferantenhäufung."""
        context = request.context

        if not context or not context.vendor_frequency or not context.total_vendor_count:
            return None

        if context.total_vendor_count == 0:
            return None

        concentration = context.vendor_frequency / context.total_vendor_count

        if concentration > self.VENDOR_CONCENTRATION_THRESHOLD:
            return RiskFinding(
                indicator=RiskIndicator.VENDOR_CLUSTERING,
                severity=Severity.LOW,
                description=f"Auffällige Häufung von Lieferant '{request.vendor_name}'",
                evidence=f"{context.vendor_frequency} von {context.total_vendor_count} Rechnungen ({concentration:.0%})",
                recommendation="Prüfung auf wirtschaftliche Abhängigkeit oder fehlende Ausschreibung",
            )

        return None

    def _check_missing_period(
        self, request: RiskAssessmentRequest
    ) -> Optional[RiskFinding]:
        """Prüft auf fehlenden Leistungszeitraum."""
        if not request.service_period_start and not request.service_period_end:
            return RiskFinding(
                indicator=RiskIndicator.MISSING_PERIOD,
                severity=Severity.LOW,
                description="Fehlende Angabe des Leistungszeitraums",
                evidence="Weder Start- noch Enddatum des Leistungszeitraums auf Rechnung",
                recommendation="Leistungszeitraum nachfordern für zeitliche Zuordnung",
            )
        return None

    def _check_round_amount(
        self, request: RiskAssessmentRequest
    ) -> Optional[RiskFinding]:
        """Prüft auf runde Pauschalbeträge."""
        amount = request.net_amount

        # Nur bei höheren Beträgen relevant
        if amount < self.ROUND_AMOUNT_THRESHOLD:
            return None

        # Prüfe auf runden Betrag (durch 100 teilbar, keine Centbeträge)
        if amount == int(amount) and int(amount) % 100 == 0:
            # Zusätzlich: Beschreibung auf Pauschal-Hinweise prüfen
            desc_lower = request.description.lower()
            pauschal_terms = ["pauschale", "pauschal", "festpreis", "einmalzahlung"]
            is_pauschal = any(term in desc_lower for term in pauschal_terms)

            severity = Severity.INFO if is_pauschal else Severity.LOW

            return RiskFinding(
                indicator=RiskIndicator.ROUND_AMOUNT,
                severity=severity,
                description=f"Runder Pauschalbetrag: {amount:.2f} EUR",
                evidence="Betrag ist ein glatter Hunderter-Betrag" + (" mit Pauschal-Hinweis" if is_pauschal else " ohne detaillierte Aufschlüsselung"),
                recommendation="Kalkulation oder Aufschlüsselung des Betrags anfordern" if not is_pauschal else "Pauschalvereinbarung dokumentieren",
            )

        return None

    def _check_outside_project_period(
        self, request: RiskAssessmentRequest
    ) -> Optional[RiskFinding]:
        """Prüft ob Leistung außerhalb Projektzeitraum liegt."""
        context = request.context

        if not context or not context.project_start or not context.project_end:
            return None

        # Leistungszeitraum oder Rechnungsdatum verwenden
        check_start = request.service_period_start or request.invoice_date
        check_end = request.service_period_end or request.invoice_date

        if check_start < context.project_start:
            return RiskFinding(
                indicator=RiskIndicator.OUTSIDE_PROJECT_PERIOD,
                severity=Severity.HIGH,
                description="Leistung beginnt vor Projektstart",
                evidence=f"Leistungsbeginn: {check_start}, Projektstart: {context.project_start}",
                recommendation="Förderfähigkeit der Leistung prüfen",
            )

        if check_end > context.project_end:
            return RiskFinding(
                indicator=RiskIndicator.OUTSIDE_PROJECT_PERIOD,
                severity=Severity.HIGH,
                description="Leistung endet nach Projektende",
                evidence=f"Leistungsende: {check_end}, Projektende: {context.project_end}",
                recommendation="Förderfähigkeit der Leistung prüfen",
            )

        return None

    def _check_project_reference(
        self, request: RiskAssessmentRequest
    ) -> Optional[RiskFinding]:
        """Prüft auf fehlenden Projektbezug in Beschreibung."""
        desc_lower = request.description.lower()

        # Generische Begriffe ohne spezifischen Bezug
        generic_patterns = [
            r"^diverse[rs]?\s",
            r"^sonstige[rs]?\s",
            r"^verschiedene\s",
            r"^allgemeine\s",
            r"\bnach aufwand\b",
            r"\bpauschale\s+leistung",
        ]

        for pattern in generic_patterns:
            if re.search(pattern, desc_lower):
                return RiskFinding(
                    indicator=RiskIndicator.NO_PROJECT_REFERENCE,
                    severity=Severity.LOW,
                    description="Generische Leistungsbeschreibung ohne erkennbaren Projektbezug",
                    evidence=f"Erkanntes Muster: '{pattern.replace(chr(92), '')}' in Beschreibung",
                    recommendation="Konkrete Projektbezug in Leistungsbeschreibung anfordern",
                )

        return None

    def _check_recipient_mismatch(
        self, request: RiskAssessmentRequest
    ) -> Optional[RiskFinding]:
        """Prüft auf Abweichung Empfänger/Begünstigter."""
        if not request.invoice_recipient or not request.beneficiary_name:
            return None

        recipient = request.invoice_recipient.lower().strip()
        beneficiary = request.beneficiary_name.lower().strip()

        # Einfacher Vergleich (detailliertere Prüfung im GrantPurposeChecker)
        if recipient != beneficiary and beneficiary not in recipient and recipient not in beneficiary:
            return RiskFinding(
                indicator=RiskIndicator.RECIPIENT_MISMATCH,
                severity=Severity.MEDIUM,
                description="Rechnungsempfänger weicht vom Begünstigten ab",
                evidence=f"Empfänger: '{request.invoice_recipient}', Begünstigter: '{request.beneficiary_name}'",
                recommendation="Prüfung ob Rechnung dem richtigen Projekt zugeordnet ist",
            )

        return None

    def _calculate_risk_score(self, findings: list[RiskFinding]) -> float:
        """Berechnet aggregierten Risiko-Score."""
        if not findings:
            return 0.0

        severity_weights = {
            Severity.INFO: 0.1,
            Severity.LOW: 0.2,
            Severity.MEDIUM: 0.4,
            Severity.HIGH: 0.7,
            Severity.CRITICAL: 1.0,
        }

        total_weight = sum(severity_weights.get(f.severity, 0.5) for f in findings)

        # Normalisieren auf 0-1 (max 5 Findings mit CRITICAL = 5.0)
        return min(total_weight / 5.0, 1.0)

    def _get_highest_severity(
        self, findings: list[RiskFinding]
    ) -> Optional[Severity]:
        """Ermittelt höchsten Schweregrad."""
        if not findings:
            return None

        severity_order = [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO,
        ]

        for severity in severity_order:
            if any(f.severity == severity for f in findings):
                return severity

        return None

    def _build_summary(self, findings: list[RiskFinding]) -> str:
        """Erstellt Zusammenfassung der Risikobewertung."""
        if not findings:
            return "Keine besonderen Risiken erkannt"

        count = len(findings)
        highest = self._get_highest_severity(findings)

        severity_text = {
            Severity.INFO: "informativer",
            Severity.LOW: "geringer",
            Severity.MEDIUM: "mittlerer",
            Severity.HIGH: "hoher",
            Severity.CRITICAL: "kritischer",
        }

        sev_str = severity_text.get(highest, "unbekannter") if highest else "unbekannter"

        if count == 1:
            return f"1 Risiko mit {sev_str} Priorität erkannt"
        return f"{count} Risiken erkannt, höchste Priorität: {sev_str}"


# Singleton-Instanz
risk_checker = RiskChecker()
