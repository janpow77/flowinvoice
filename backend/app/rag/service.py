# Pfad: /backend/app/rag/service.py
"""
FlowAudit RAG Service

Few-Shot-Learning Service für Rechnungsprüfung.
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.services.parser import ParseResult
from app.services.rule_engine import PrecheckResult

from .vectorstore import VectorStore, get_vectorstore

logger = logging.getLogger(__name__)


@dataclass
class FewShotExample:
    """Few-Shot-Beispiel für LLM-Prompt."""

    example_type: str  # "invoice", "error", "pattern"
    content: str
    metadata: dict[str, Any]
    relevance_score: float


@dataclass
class RAGContext:
    """RAG-Kontext für LLM-Analyse."""

    similar_invoices: list[FewShotExample]
    error_corrections: list[FewShotExample]
    semantic_patterns: list[FewShotExample]
    total_examples: int


class RAGService:
    """
    RAG Service für Few-Shot-Learning.

    Verwendet ChromaDB zur Suche nach:
    - Ähnlichen validierten Rechnungen
    - Fehlerbeispielen mit Korrekturen
    - Semantischen Mustern
    """

    def __init__(self, vectorstore: VectorStore | None = None):
        """
        Initialisiert RAG Service.

        Args:
            vectorstore: VectorStore-Instanz
        """
        self._vectorstore = vectorstore or get_vectorstore()

    def get_context_for_analysis(
        self,
        parse_result: ParseResult,
        precheck_result: PrecheckResult,
        project_context: dict[str, Any] | None = None,
        max_examples: int = 5,
    ) -> RAGContext:
        """
        Erstellt RAG-Kontext für LLM-Analyse.

        Args:
            parse_result: Parse-Ergebnis
            precheck_result: Vorprüfungsergebnis
            project_context: Projekt-Kontext
            max_examples: Max. Anzahl Beispiele

        Returns:
            RAGContext mit Few-Shot-Beispielen
        """
        similar_invoices: list[FewShotExample] = []
        error_corrections: list[FewShotExample] = []
        semantic_patterns: list[FewShotExample] = []

        # 1. Ähnliche Rechnungen suchen
        invoice_results = self._vectorstore.find_similar_invoices(
            raw_text=parse_result.raw_text,
            extracted_data={
                k: v.value for k, v in parse_result.extracted.items()
            },
            n_results=max_examples,
            ruleset_id=precheck_result.ruleset_id,
        )

        for result in invoice_results:
            if result.score > 0.5:  # Relevanz-Schwelle
                similar_invoices.append(FewShotExample(
                    example_type="invoice",
                    content=result.document,
                    metadata=result.metadata,
                    relevance_score=result.score,
                ))

        # 2. Fehlerbeispiele für gefundene Fehler suchen
        for error in precheck_result.errors[:3]:  # Max 3 Fehler
            error_results = self._vectorstore.find_similar_errors(
                error_type=error.error_type.value if error.error_type else "UNKNOWN",
                feature_id=error.feature_id,
                context_text=parse_result.raw_text[:500],
                n_results=2,
                ruleset_id=precheck_result.ruleset_id,
            )

            for result in error_results:
                if result.score > 0.4:
                    error_corrections.append(FewShotExample(
                        example_type="error",
                        content=result.document,
                        metadata={
                            **result.metadata,
                            "related_error": error.feature_id,
                        },
                        relevance_score=result.score,
                    ))

        # 3. Semantische Muster für Leistungsbeschreibung
        supply_desc = parse_result.extracted.get("supply_description")
        if supply_desc and supply_desc.value:
            pattern_results = self._vectorstore.find_matching_patterns(
                text=str(supply_desc.value),
                pattern_type="supply_description",
                n_results=3,
            )

            for result in pattern_results:
                if result.score > 0.3:
                    semantic_patterns.append(FewShotExample(
                        example_type="pattern",
                        content=result.document,
                        metadata=result.metadata,
                        relevance_score=result.score,
                    ))

        # 4. Red-Flag-Muster prüfen
        red_flag_results = self._vectorstore.find_matching_patterns(
            text=parse_result.raw_text[:1500],
            pattern_type="economic_red_flag",
            n_results=2,
        )

        for result in red_flag_results:
            if result.score > 0.6:  # Höhere Schwelle für Red Flags
                semantic_patterns.append(FewShotExample(
                    example_type="red_flag",
                    content=result.document,
                    metadata=result.metadata,
                    relevance_score=result.score,
                ))

        return RAGContext(
            similar_invoices=similar_invoices,
            error_corrections=error_corrections,
            semantic_patterns=semantic_patterns,
            total_examples=len(similar_invoices) + len(error_corrections) + len(semantic_patterns),
        )

    def format_context_for_prompt(
        self,
        rag_context: RAGContext,
        max_chars: int = 4000,
    ) -> str:
        """
        Formatiert RAG-Kontext für LLM-Prompt.

        Args:
            rag_context: RAG-Kontext
            max_chars: Max. Zeichen

        Returns:
            Formatierter Text für Prompt
        """
        parts: list[str] = []
        current_chars = 0

        # Ähnliche Rechnungen
        if rag_context.similar_invoices:
            parts.append("=== ÄHNLICHE RECHNUNGEN (validiert) ===")
            for i, example in enumerate(rag_context.similar_invoices[:2], 1):
                example_text = self._format_invoice_example(example, i)
                if current_chars + len(example_text) > max_chars:
                    break
                parts.append(example_text)
                current_chars += len(example_text)

        # Fehlerbeispiele
        if rag_context.error_corrections:
            parts.append("\n=== FEHLERBEISPIELE MIT KORREKTUREN ===")
            for i, example in enumerate(rag_context.error_corrections[:2], 1):
                example_text = self._format_error_example(example, i)
                if current_chars + len(example_text) > max_chars:
                    break
                parts.append(example_text)
                current_chars += len(example_text)

        # Semantische Muster
        if rag_context.semantic_patterns:
            parts.append("\n=== RELEVANTE MUSTER ===")
            for example in rag_context.semantic_patterns[:2]:
                example_text = self._format_pattern_example(example)
                if current_chars + len(example_text) > max_chars:
                    break
                parts.append(example_text)
                current_chars += len(example_text)

        return "\n".join(parts)

    def _format_invoice_example(self, example: FewShotExample, index: int) -> str:
        """Formatiert Rechnungsbeispiel."""
        assessment = example.metadata.get("assessment", "unknown")
        has_errors = example.metadata.get("has_errors", False)

        return f"""
Beispiel {index} (Bewertung: {assessment}, Fehler: {'ja' if has_errors else 'nein'}):
{example.content[:500]}
---"""

    def _format_error_example(self, example: FewShotExample, index: int) -> str:
        """Formatiert Fehlerbeispiel."""
        error_type = example.metadata.get("error_type", "unknown")
        feature_id = example.metadata.get("feature_id", "unknown")
        correct_value = example.metadata.get("correct_value", "")

        return f"""
Fehlerbeispiel {index}:
- Feature: {feature_id}
- Fehlertyp: {error_type}
- Korrektur: {correct_value}
{example.content[:300]}
---"""

    def _format_pattern_example(self, example: FewShotExample) -> str:
        """Formatiert Musterbeispiel."""
        pattern_type = example.metadata.get("pattern_type", "unknown")
        description = example.metadata.get("description", "")

        return f"""
Muster ({pattern_type}):
{description}
---"""

    # =========================================================================
    # Learning from Feedback
    # =========================================================================

    def learn_from_validation(
        self,
        document_id: str,
        parse_result: ParseResult,
        final_assessment: str,
        corrections: list[dict[str, Any]] | None = None,
        ruleset_id: str = "DE_USTG",
        chunking_config: dict | None = None,
    ):
        """
        Lernt aus validierter Rechnung.

        Args:
            document_id: Dokument-ID
            parse_result: Parse-Ergebnis
            final_assessment: Finale Bewertung
            corrections: Korrekturen durch Benutzer
            ruleset_id: Ruleset
            chunking_config: Optional Chunking-Konfiguration vom Dokumenttyp
        """
        # Rechnung als Beispiel speichern (mit optionalem Chunking)
        self._vectorstore.add_invoice_example(
            document_id=document_id,
            raw_text=parse_result.raw_text,
            extracted_data={
                k: v.value for k, v in parse_result.extracted.items()
            },
            assessment=final_assessment,
            errors=corrections,
            ruleset_id=ruleset_id,
            chunking_config=chunking_config,
        )

        # Korrekturen als Fehlerbeispiele speichern
        if corrections:
            for i, correction in enumerate(corrections):
                error_id = f"{document_id}_error_{i}"
                self._vectorstore.add_error_example(
                    error_id=error_id,
                    error_type=correction.get("error_type", "UNKNOWN"),
                    feature_id=correction.get("feature_id", ""),
                    context_text=correction.get("context", parse_result.raw_text[:500]),
                    wrong_value=correction.get("wrong_value", ""),
                    correct_value=correction.get("correct_value", ""),
                    reasoning=correction.get("reasoning", ""),
                    ruleset_id=ruleset_id,
                )

        logger.info(f"Learned from document: {document_id}")

    def add_semantic_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        description: str,
        examples: list[str],
        project_type: str | None = None,
    ):
        """
        Fügt semantisches Muster hinzu.

        Args:
            pattern_id: Pattern-ID
            pattern_type: Mustertyp
            description: Beschreibung
            examples: Beispieltexte
            project_type: Projekttyp
        """
        self._vectorstore.add_pattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            description=description,
            examples=examples,
            project_type=project_type,
        )

    def get_stats(self) -> dict[str, Any]:
        """Gibt RAG-Statistiken zurück."""
        return {
            "collections": self._vectorstore.get_collection_stats(),
        }


# Singleton
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """
    Gibt RAG-Service-Singleton zurück.

    Returns:
        RAGService-Instanz
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def init_default_patterns():
    """Initialisiert Standard-Muster für RAG."""
    service = get_rag_service()

    # Red-Flag-Muster für wirtschaftliche Prüfung
    red_flags = [
        {
            "id": "red_flag_luxury",
            "type": "economic_red_flag",
            "description": "Luxusgüter ohne Projektbezug",
            "examples": [
                "Strandliegen",
                "Wellnessbehandlung",
                "Champagner",
                "Luxushotel",
            ],
        },
        {
            "id": "red_flag_entertainment",
            "type": "economic_red_flag",
            "description": "Unterhaltung ohne Projektbezug",
            "examples": [
                "Konzerttickets",
                "Freizeitpark",
                "Sportveranstaltung",
            ],
        },
        {
            "id": "red_flag_personal",
            "type": "economic_red_flag",
            "description": "Persönliche Ausgaben",
            "examples": [
                "Privatreise",
                "Geschenke privat",
                "Kleidung",
            ],
        },
    ]

    for rf in red_flags:
        service.add_semantic_pattern(
            pattern_id=rf["id"],
            pattern_type=rf["type"],
            description=rf["description"],
            examples=rf["examples"],
        )

    # Typische Leistungsbeschreibungen nach Projekttyp
    supply_patterns = [
        {
            "id": "supply_it_project",
            "type": "supply_description",
            "description": "IT-Projektleistungen",
            "examples": [
                "Softwareentwicklung",
                "Programmierung",
                "IT-Beratung",
                "Cloud-Services",
                "Serverhosting",
            ],
            "project_type": "IT",
        },
        {
            "id": "supply_research",
            "type": "supply_description",
            "description": "Forschungsleistungen",
            "examples": [
                "Laboranalyse",
                "Studienteilnahme",
                "Forschungsmaterial",
                "Wissenschaftliche Beratung",
            ],
            "project_type": "RESEARCH",
        },
        {
            "id": "supply_event",
            "type": "supply_description",
            "description": "Veranstaltungsleistungen",
            "examples": [
                "Konferenzraum",
                "Catering",
                "Technik-Verleih",
                "Moderationsleistung",
            ],
            "project_type": "EVENT",
        },
    ]

    for sp in supply_patterns:
        service.add_semantic_pattern(
            pattern_id=sp["id"],
            pattern_type=sp["type"],
            description=sp["description"],
            examples=sp["examples"],
            project_type=sp.get("project_type"),
        )

    logger.info("Initialized default RAG patterns")
