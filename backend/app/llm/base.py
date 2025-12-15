# Pfad: /backend/app/llm/base.py
"""
FlowAudit LLM Base

Abstrakte Basisklasse für LLM-Provider.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.models.enums import Provider

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    """Nachricht für LLM-Konversation."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMRequest:
    """Request an LLM."""

    messages: list[LLMMessage]
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    json_mode: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response vom LLM."""

    content: str
    model: str
    provider: Provider
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    raw_response: dict[str, Any] | None = None
    error: str | None = None


class BaseLLMProvider(ABC):
    """
    Abstrakte Basisklasse für LLM-Provider.

    Alle Provider (Ollama, OpenAI, Anthropic, Gemini)
    implementieren dieses Interface.
    """

    provider: Provider
    default_model: str

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Führt Completion durch.

        Args:
            request: LLMRequest

        Returns:
            LLMResponse
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Prüft ob Provider erreichbar.

        Returns:
            True wenn erreichbar
        """

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """
        Gibt verfügbare Modelle zurück.

        Returns:
            Liste der Modell-IDs
        """

    def _build_system_prompt(self, ruleset_id: str, extracted_data: dict[str, Any]) -> str:
        """
        Erstellt System-Prompt für Rechnungsprüfung.

        Args:
            ruleset_id: Ruleset-ID
            extracted_data: Extrahierte Daten

        Returns:
            System-Prompt
        """
        return f"""Du bist ein Experte für steuerliche Rechnungsprüfung.
Deine Aufgabe ist die Prüfung von Rechnungen nach dem Regelwerk {ruleset_id}.

WICHTIG:
- Antworte IMMER auf Deutsch
- Antworte im JSON-Format
- Sei präzise und verweise auf konkrete Rechtsgrundlagen
- Prüfe nur die angegebenen Merkmale

KONTEXT:
Die Rechnung wurde bereits vorgeprüft. Folgende Daten wurden extrahiert:
{extracted_data}

Deine Aufgabe:
1. Prüfe semantische Plausibilität der Leistungsbeschreibung
2. Identifiziere mögliche Unstimmigkeiten
3. Bewerte wirtschaftliche Angemessenheit
"""

    def _build_user_prompt(
        self,
        raw_text: str,
        project_context: dict[str, Any] | None = None,
        beneficiary_context: dict[str, Any] | None = None,
    ) -> str:
        """
        Erstellt User-Prompt.

        Args:
            raw_text: Roh-Text der Rechnung
            project_context: Projekt-Kontext
            beneficiary_context: Begünstigten-Kontext

        Returns:
            User-Prompt
        """
        prompt_parts = [
            "Bitte prüfe die folgende Rechnung:",
            "",
            "--- RECHNUNGSTEXT ---",
            raw_text[:8000],  # Limit für Kontext
            "--- ENDE RECHNUNGSTEXT ---",
        ]

        if project_context:
            prompt_parts.extend([
                "",
                "--- PROJEKTKONTEXT ---",
                f"Projekttitel: {project_context.get('title', 'N/A')}",
                f"Projektzeitraum: {project_context.get('start_date', 'N/A')} - {project_context.get('end_date', 'N/A')}",
                f"Projektbeschreibung: {project_context.get('description', 'N/A')}",
                "--- ENDE PROJEKTKONTEXT ---",
            ])

        if beneficiary_context:
            prompt_parts.extend([
                "",
                "--- BEGÜNSTIGTENKONTEXT ---",
                f"Name: {beneficiary_context.get('name', 'N/A')}",
                f"Adresse: {beneficiary_context.get('address', 'N/A')}",
                f"Aliase: {', '.join(beneficiary_context.get('aliases', []))}",
                "--- ENDE BEGÜNSTIGTENKONTEXT ---",
            ])

        prompt_parts.extend([
            "",
            "Antworte im folgenden JSON-Format:",
            """{
  "semantic_check": {
    "supply_fits_project": "yes|partial|unclear|no",
    "supply_description_quality": "clear|vague|missing",
    "reasoning": "..."
  },
  "economic_check": {
    "reasonable": "yes|questionable|no",
    "reasoning": "..."
  },
  "beneficiary_match": {
    "matches": "yes|partial|no",
    "detected_name": "...",
    "reasoning": "..."
  },
  "warnings": [
    {"type": "...", "message": "...", "severity": "low|medium|high"}
  ],
  "overall_assessment": "ok|review_needed|reject",
  "confidence": 0.0-1.0
}""",
        ])

        return "\n".join(prompt_parts)
