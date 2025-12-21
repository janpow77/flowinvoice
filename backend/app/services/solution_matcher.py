# Pfad: /backend/app/services/solution_matcher.py
"""
Solution File Matcher

Matched Lösungsdatei-Einträge zu hochgeladenen Dokumenten.
Unterstützt verschiedene Matching-Strategien.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from app.models.enums import MatchingStrategy
from app.services.solution_parser import ParsedSolutionFile, SolutionEntry

logger = logging.getLogger(__name__)


@dataclass
class DocumentInfo:
    """Information über ein hochgeladenes Dokument."""

    document_id: str
    filename: str
    upload_position: int  # Position in der Upload-Reihenfolge (1-basiert)
    upload_time: datetime | None = None

    # Optionale extrahierte Daten für erweitertes Matching
    invoice_number: str | None = None
    invoice_date: str | None = None
    net_amount: float | None = None


@dataclass
class MatchResult:
    """Ergebnis eines Matchings zwischen Dokument und Lösungseintrag."""

    document_id: str
    document_filename: str
    solution_entry: SolutionEntry
    match_confidence: float  # 0.0 - 1.0
    match_reason: str
    strategy_used: MatchingStrategy

    @property
    def is_confident_match(self) -> bool:
        """Prüft ob es ein sicheres Match ist (>80% Konfidenz)."""
        return self.match_confidence >= 0.8


@dataclass
class MatchingResult:
    """Gesamtergebnis des Matchings."""

    matched: list[MatchResult] = field(default_factory=list)
    unmatched_documents: list[DocumentInfo] = field(default_factory=list)
    unmatched_solutions: list[SolutionEntry] = field(default_factory=list)
    strategy: MatchingStrategy = MatchingStrategy.FILENAME_POSITION

    @property
    def match_count(self) -> int:
        """Anzahl gematchter Dokumente."""
        return len(self.matched)

    @property
    def total_documents(self) -> int:
        """Gesamtanzahl Dokumente."""
        return len(self.matched) + len(self.unmatched_documents)

    @property
    def match_rate(self) -> float:
        """Match-Rate (0.0 - 1.0)."""
        if self.total_documents == 0:
            return 0.0
        return self.match_count / self.total_documents

    def get_match_for_document(self, document_id: str) -> MatchResult | None:
        """Findet Match für ein Dokument."""
        for match in self.matched:
            if match.document_id == document_id:
                return match
        return None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "matched_count": self.match_count,
            "unmatched_documents": len(self.unmatched_documents),
            "unmatched_solutions": len(self.unmatched_solutions),
            "match_rate": self.match_rate,
            "strategy": self.strategy.value,
            "matches": [
                {
                    "document_id": m.document_id,
                    "document_filename": m.document_filename,
                    "solution_filename": m.solution_entry.filename,
                    "solution_position": m.solution_entry.position,
                    "is_valid": m.solution_entry.is_valid,
                    "error_count": len(m.solution_entry.errors),
                    "confidence": m.match_confidence,
                    "reason": m.match_reason,
                }
                for m in self.matched
            ],
        }


class SolutionMatcher:
    """
    Matched Lösungsdatei-Einträge zu Dokumenten.

    Strategien:
    - FILENAME: Exakter Dateiname-Match
    - FILENAME_POSITION: Dateiname + Position für Disambiguierung
    - POSITION_ONLY: Nur Position in Upload-Reihenfolge
    """

    def __init__(self, strategy: MatchingStrategy = MatchingStrategy.FILENAME_POSITION):
        """
        Initialisiert den Matcher.

        Args:
            strategy: Standard-Matching-Strategie
        """
        self.strategy = strategy
        self.version = "1.0.0"

    def match(
        self,
        documents: list[DocumentInfo],
        solution_file: ParsedSolutionFile,
        strategy: MatchingStrategy | None = None,
    ) -> MatchingResult:
        """
        Matched Dokumente zu Lösungsdatei-Einträgen.

        Args:
            documents: Liste der hochgeladenen Dokumente
            solution_file: Geparste Lösungsdatei
            strategy: Optionale Strategie-Überschreibung

        Returns:
            Matching-Ergebnis
        """
        used_strategy = strategy or self.strategy

        if used_strategy == MatchingStrategy.FILENAME:
            return self._match_by_filename(documents, solution_file)
        elif used_strategy == MatchingStrategy.FILENAME_POSITION:
            return self._match_by_filename_position(documents, solution_file)
        elif used_strategy == MatchingStrategy.POSITION_ONLY:
            return self._match_by_position(documents, solution_file)
        else:
            raise ValueError(f"Unbekannte Strategie: {used_strategy}")

    def _match_by_filename(
        self,
        documents: list[DocumentInfo],
        solution_file: ParsedSolutionFile,
    ) -> MatchingResult:
        """Matched ausschließlich nach Dateiname."""
        result = MatchingResult(strategy=MatchingStrategy.FILENAME)

        # Lösungsdatei nach Dateiname indizieren
        solution_by_filename: dict[str, SolutionEntry] = {}
        for entry in solution_file.entries:
            normalized_name = self._normalize_filename(entry.filename)
            solution_by_filename[normalized_name] = entry

        used_solutions: set[int] = set()

        for doc in documents:
            doc_filename = self._normalize_filename(doc.filename)

            # Exakter Match
            if doc_filename in solution_by_filename:
                entry = solution_by_filename[doc_filename]
                result.matched.append(MatchResult(
                    document_id=doc.document_id,
                    document_filename=doc.filename,
                    solution_entry=entry,
                    match_confidence=1.0,
                    match_reason="Exakter Dateiname-Match",
                    strategy_used=MatchingStrategy.FILENAME,
                ))
                used_solutions.add(entry.position)
            else:
                # Fuzzy-Match versuchen
                best_match = self._find_fuzzy_match(doc_filename, solution_file.entries, used_solutions)
                if best_match:
                    entry, confidence = best_match
                    result.matched.append(MatchResult(
                        document_id=doc.document_id,
                        document_filename=doc.filename,
                        solution_entry=entry,
                        match_confidence=confidence,
                        match_reason=f"Ähnlicher Dateiname (Konfidenz: {confidence:.0%})",
                        strategy_used=MatchingStrategy.FILENAME,
                    ))
                    used_solutions.add(entry.position)
                else:
                    result.unmatched_documents.append(doc)

        # Nicht gematchte Lösungen sammeln
        for entry in solution_file.entries:
            if entry.position not in used_solutions:
                result.unmatched_solutions.append(entry)

        return result

    def _match_by_filename_position(
        self,
        documents: list[DocumentInfo],
        solution_file: ParsedSolutionFile,
    ) -> MatchingResult:
        """Matched nach Dateiname mit Position für Disambiguierung."""
        result = MatchingResult(strategy=MatchingStrategy.FILENAME_POSITION)

        # Dokumente nach Position sortieren
        sorted_docs = sorted(documents, key=lambda d: d.upload_position)

        # Lösungsdatei nach Dateiname gruppieren (für Mehrfach-Matches)
        solution_by_filename: dict[str, list[SolutionEntry]] = {}
        for entry in solution_file.entries:
            normalized_name = self._normalize_filename(entry.filename)
            if normalized_name not in solution_by_filename:
                solution_by_filename[normalized_name] = []
            solution_by_filename[normalized_name].append(entry)

        used_solutions: set[int] = set()

        for doc in sorted_docs:
            doc_filename = self._normalize_filename(doc.filename)

            if doc_filename in solution_by_filename:
                # Alle Matches für diesen Dateinamen
                candidates = [e for e in solution_by_filename[doc_filename] if e.position not in used_solutions]

                if len(candidates) == 1:
                    # Eindeutiger Match
                    entry = candidates[0]
                    result.matched.append(MatchResult(
                        document_id=doc.document_id,
                        document_filename=doc.filename,
                        solution_entry=entry,
                        match_confidence=1.0,
                        match_reason="Eindeutiger Dateiname-Match",
                        strategy_used=MatchingStrategy.FILENAME_POSITION,
                    ))
                    used_solutions.add(entry.position)
                elif len(candidates) > 1:
                    # Mehrere Kandidaten -> Position verwenden
                    best = min(candidates, key=lambda e: abs(e.position - doc.upload_position))
                    confidence = 0.9 if best.position == doc.upload_position else 0.7
                    result.matched.append(MatchResult(
                        document_id=doc.document_id,
                        document_filename=doc.filename,
                        solution_entry=best,
                        match_confidence=confidence,
                        match_reason=f"Dateiname + Position-Match (Position {best.position})",
                        strategy_used=MatchingStrategy.FILENAME_POSITION,
                    ))
                    used_solutions.add(best.position)
                else:
                    # Kein Kandidat mehr verfügbar
                    result.unmatched_documents.append(doc)
            else:
                # Kein Dateiname-Match -> Fallback auf Position
                position_match = solution_file.get_entry_by_position(doc.upload_position)
                if position_match and position_match.position not in used_solutions:
                    result.matched.append(MatchResult(
                        document_id=doc.document_id,
                        document_filename=doc.filename,
                        solution_entry=position_match,
                        match_confidence=0.6,
                        match_reason=f"Position-Fallback (Position {position_match.position})",
                        strategy_used=MatchingStrategy.FILENAME_POSITION,
                    ))
                    used_solutions.add(position_match.position)
                else:
                    result.unmatched_documents.append(doc)

        # Nicht gematchte Lösungen sammeln
        for entry in solution_file.entries:
            if entry.position not in used_solutions:
                result.unmatched_solutions.append(entry)

        return result

    def _match_by_position(
        self,
        documents: list[DocumentInfo],
        solution_file: ParsedSolutionFile,
    ) -> MatchingResult:
        """Matched ausschließlich nach Position."""
        result = MatchingResult(strategy=MatchingStrategy.POSITION_ONLY)

        # Dokumente nach Position sortieren
        sorted_docs = sorted(documents, key=lambda d: d.upload_position)

        for doc in sorted_docs:
            entry = solution_file.get_entry_by_position(doc.upload_position)
            if entry:
                result.matched.append(MatchResult(
                    document_id=doc.document_id,
                    document_filename=doc.filename,
                    solution_entry=entry,
                    match_confidence=0.8,
                    match_reason=f"Position-Match (Position {entry.position})",
                    strategy_used=MatchingStrategy.POSITION_ONLY,
                ))
            else:
                result.unmatched_documents.append(doc)

        # Nicht gematchte Lösungen (mehr Lösungen als Dokumente)
        matched_positions = {m.solution_entry.position for m in result.matched}
        for entry in solution_file.entries:
            if entry.position not in matched_positions:
                result.unmatched_solutions.append(entry)

        return result

    def _normalize_filename(self, filename: str) -> str:
        """Normalisiert einen Dateinamen für Vergleiche."""
        # Pfad entfernen, nur Dateiname
        name = Path(filename).name

        # Lowercase
        name = name.lower()

        # Erweiterung entfernen
        name = Path(name).stem

        # Sonderzeichen normalisieren
        name = re.sub(r"[_\-\s]+", "_", name)

        # Trailing/Leading underscores entfernen
        name = name.strip("_")

        return name

    def _find_fuzzy_match(
        self,
        filename: str,
        entries: list[SolutionEntry],
        used_positions: set[int],
        threshold: float = 0.7,
    ) -> tuple[SolutionEntry, float] | None:
        """
        Findet einen Fuzzy-Match für einen Dateinamen.

        Args:
            filename: Normalisierter Dateiname
            entries: Lösungsdatei-Einträge
            used_positions: Bereits verwendete Positionen
            threshold: Mindest-Ähnlichkeit

        Returns:
            Bestes Match mit Konfidenz oder None
        """
        best_entry: SolutionEntry | None = None
        best_ratio = 0.0

        for entry in entries:
            if entry.position in used_positions:
                continue

            entry_filename = self._normalize_filename(entry.filename)
            ratio = SequenceMatcher(None, filename, entry_filename).ratio()

            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_entry = entry

        if best_entry:
            return (best_entry, best_ratio)
        return None


# Singleton-Instanz
solution_matcher = SolutionMatcher()
