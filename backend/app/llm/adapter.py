# Pfad: /backend/app/llm/adapter.py
"""
FlowAudit LLM Adapter

Zentraler Adapter für alle LLM-Provider.
Ermöglicht transparenten Provider-Wechsel.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Provider
from app.models.ruleset import Ruleset
from app.services.parser import ParseResult
from app.services.rule_engine import PrecheckResult, get_rule_engine

from .anthropic import AnthropicProvider
from .base import BaseLLMProvider, LLMMessage, LLMRequest, LLMResponse
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider

logger = logging.getLogger(__name__)


def _strip_markdown_fences(text: str) -> str:
    """
    Entfernt Markdown-Code-Fences aus LLM-Responses.

    LLMs antworten oft mit ```json ... ``` obwohl json_mode aktiv ist.
    Diese Funktion entfernt solche Wrapper sicher.

    Args:
        text: Rohe LLM-Antwort

    Returns:
        Bereinigter JSON-String
    """
    text = text.strip()

    # Pattern für Code-Fences (```json, ```, etc.)
    fence_pattern = r'^```(?:json|JSON)?\s*\n?(.*?)\n?```$'
    match = re.match(fence_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Fallback: Einfache Fence-Entfernung am Anfang/Ende
    if text.startswith("```"):
        # Erste Zeile (```json oder ```) entfernen
        lines = text.split("\n", 1)
        if len(lines) > 1:
            text = lines[1]

    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]

    return text.strip()


@dataclass
class InvoiceAnalysisRequest:
    """Request für Rechnungsanalyse."""

    parse_result: ParseResult
    precheck_result: PrecheckResult
    ruleset_id: str = "DE_USTG"
    project_context: dict[str, Any] | None = None
    beneficiary_context: dict[str, Any] | None = None
    rag_examples: list[dict[str, Any]] | None = None
    legal_context: list[dict[str, Any]] | None = None


@dataclass
class InvoiceAnalysisResult:
    """Ergebnis der LLM-Analyse."""

    semantic_check: dict[str, Any]
    economic_check: dict[str, Any]
    beneficiary_match: dict[str, Any]
    warnings: list[dict[str, Any]]
    overall_assessment: str
    confidence: float
    llm_response: LLMResponse
    raw_json: dict[str, Any] | None = None


class LLMAdapter:
    """
    Zentraler LLM-Adapter.

    Verwaltet alle Provider und ermöglicht:
    - Provider-Auswahl
    - Fallback bei Fehlern
    - Einheitliche Schnittstelle
    """

    def __init__(self):
        """Initialisiert Adapter mit allen Providern."""
        self._providers: dict[Provider, BaseLLMProvider] = {}
        self._default_provider = Provider.LOCAL_OLLAMA

    def register_provider(self, provider: BaseLLMProvider):
        """
        Registriert Provider.

        Args:
            provider: Provider-Instanz
        """
        self._providers[provider.provider] = provider
        logger.info(f"Registered LLM provider: {provider.provider}")

    def get_provider(self, provider_type: Provider) -> BaseLLMProvider | None:
        """
        Gibt Provider zurück.

        Args:
            provider_type: Provider-Typ

        Returns:
            Provider oder None
        """
        return self._providers.get(provider_type)

    def set_default_provider(self, provider_type: Provider):
        """
        Setzt Standard-Provider.

        Args:
            provider_type: Provider-Typ
        """
        if provider_type in self._providers:
            self._default_provider = provider_type
        else:
            logger.warning(f"Provider {provider_type} not registered")

    async def complete(
        self,
        request: LLMRequest,
        provider_type: Provider | None = None,
    ) -> LLMResponse:
        """
        Führt Completion durch.

        Args:
            request: LLMRequest
            provider_type: Provider (default: Standard-Provider)

        Returns:
            LLMResponse
        """
        provider_type = provider_type or self._default_provider
        provider = self._providers.get(provider_type)

        if not provider:
            return LLMResponse(
                content="",
                model="",
                provider=provider_type,
                error=f"Provider {provider_type} nicht verfügbar",
            )

        return await provider.complete(request)

    async def analyze_invoice(
        self,
        analysis_request: InvoiceAnalysisRequest,
        provider_type: Provider | None = None,
        model: str | None = None,
        session: AsyncSession | None = None,
    ) -> InvoiceAnalysisResult:
        """
        Analysiert Rechnung mit LLM.

        Args:
            analysis_request: Analyse-Request
            provider_type: Provider
            model: Modell-ID
            session: Optional - DB-Session für Regelwerk-Lookup

        Returns:
            InvoiceAnalysisResult
        """
        provider_type = provider_type or self._default_provider
        provider = self._providers.get(provider_type)

        if not provider:
            return InvoiceAnalysisResult(
                semantic_check={},
                economic_check={},
                beneficiary_match={},
                warnings=[],
                overall_assessment="error",
                confidence=0.0,
                llm_response=LLMResponse(
                    content="",
                    model="",
                    provider=provider_type,
                    error=f"Provider {provider_type} nicht verfügbar",
                ),
            )

        # Regelwerk aus Datenbank laden, falls Session vorhanden
        db_features: list[dict[str, Any]] | None = None
        db_ruleset_info: dict[str, Any] | None = None
        if session:
            try:
                db_features, db_ruleset_info = await self._fetch_ruleset_from_db(
                    session, analysis_request.ruleset_id
                )
            except Exception as e:
                logger.warning(f"Failed to fetch ruleset from DB: {e}")

        # Prompts erstellen
        system_prompt = self._build_system_prompt(
            analysis_request.ruleset_id,
            analysis_request.precheck_result,
            analysis_request.rag_examples,
            db_features=db_features,
            db_ruleset_info=db_ruleset_info,
            legal_context=analysis_request.legal_context,
        )

        user_prompt = self._build_user_prompt(
            analysis_request.parse_result,
            analysis_request.project_context,
            analysis_request.beneficiary_context,
        )

        # LLM-Request
        llm_request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt),
            ],
            model=model,
            temperature=0.0,
            max_tokens=4096,
            json_mode=True,
        )

        # Completion durchführen
        response = await provider.complete(llm_request)

        # Response parsen
        return self._parse_analysis_response(response)

    async def _fetch_ruleset_from_db(
        self,
        session: AsyncSession,
        ruleset_id: str,
    ) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
        """
        Lädt Regelwerk aus der Datenbank.

        Args:
            session: DB-Session
            ruleset_id: Ruleset-ID

        Returns:
            Tuple von (features_list, ruleset_info) oder (None, None)
        """
        result = await session.execute(
            select(Ruleset)
            .where(Ruleset.ruleset_id == ruleset_id)
            .order_by(Ruleset.version.desc())
        )
        ruleset = result.scalar_one_or_none()

        if ruleset and ruleset.features:
            ruleset_info = {
                "title_de": ruleset.title_de,
                "title_en": ruleset.title_en,
                "jurisdiction": ruleset.jurisdiction,
                "legal_references": ruleset.legal_references or [],
            }
            return ruleset.features, ruleset_info

        return None, None

    def _format_ruleset_features(self, features: dict[str, Any]) -> str:
        """
        Formatiert Regelwerk-Features für den LLM-Prompt (aus Rule Engine).

        Args:
            features: Dict der FeatureDefinition-Objekte

        Returns:
            Formatierter String für den Prompt
        """
        lines = []
        for feature_id, feature_def in features.items():
            required = "PFLICHT" if feature_def.required_level.value == "REQUIRED" else (
                "BEDINGT" if feature_def.required_level.value == "CONDITIONAL" else "OPTIONAL"
            )
            lines.append(
                f"- {feature_def.name_de} ({feature_id}): {required} | {feature_def.legal_basis}"
            )
        return "\n".join(lines)

    def _format_db_features(self, features: list[dict[str, Any]]) -> str:
        """
        Formatiert Regelwerk-Features für den LLM-Prompt (aus Datenbank).

        Args:
            features: Liste der Feature-Dicts aus der DB

        Returns:
            Formatierter String für den Prompt
        """
        lines = []
        for feature in features:
            feature_id = feature.get("feature_id", "")
            name_de = feature.get("name_de", feature_id)
            required_level = feature.get("required_level", "OPTIONAL")
            legal_basis = feature.get("legal_basis", "")

            required = "PFLICHT" if required_level == "REQUIRED" else (
                "BEDINGT" if required_level == "CONDITIONAL" else "OPTIONAL"
            )
            lines.append(
                f"- {name_de} ({feature_id}): {required} | {legal_basis}"
            )
        return "\n".join(lines)

    def _build_system_prompt(
        self,
        ruleset_id: str,
        precheck_result: PrecheckResult,
        rag_examples: list[dict[str, Any]] | None,
        db_features: list[dict[str, Any]] | None = None,
        db_ruleset_info: dict[str, Any] | None = None,
        legal_context: list[dict[str, Any]] | None = None,
    ) -> str:
        """Erstellt System-Prompt mit Regelwerk-Features."""
        # Features aus DB oder Fallback auf hardcodierte Rule Engine
        if db_features:
            features_json = self._format_db_features(db_features)
            logger.info(f"Using database ruleset features for {ruleset_id}")
        else:
            rule_engine = get_rule_engine(ruleset_id)
            features_json = self._format_ruleset_features(rule_engine.features)
            logger.info(f"Using hardcoded ruleset features for {ruleset_id}")

        prompt_parts = [
            "Du bist ein Experte für steuerliche Rechnungsprüfung.",
            f"Deine Aufgabe ist die Prüfung von Rechnungen nach dem Regelwerk {ruleset_id}.",
            "",
            "REGELWERK-MERKMALE:",
            "Die folgenden Merkmale müssen geprüft werden:",
            features_json,
            "",
            "WICHTIG:",
            "- Antworte IMMER auf Deutsch",
            "- Antworte im JSON-Format",
            "- Sei präzise und verweise auf konkrete Rechtsgrundlagen",
            "- Nutze die deutschen Merkmalsnamen aus dem Regelwerk",
            "- Die Rechnung wurde bereits vorgeprüft. Du führst die semantische Analyse durch.",
            "",
        ]

        # Vorprüfungsergebnisse einfügen
        if precheck_result.errors:
            prompt_parts.append("VORPRÜFUNG - Gefundene Fehler:")
            for err in precheck_result.errors:
                prompt_parts.append(f"- {err.feature_id}: {err.message}")
            prompt_parts.append("")

        if precheck_result.is_small_amount:
            prompt_parts.append("HINWEIS: Kleinbetragsrechnung (§ 33 UStDV)")
            prompt_parts.append("")

        # RAG-Beispiele einfügen (Few-Shot)
        if rag_examples:
            prompt_parts.append("REFERENZBEISPIELE für ähnliche Fälle:")
            for i, example in enumerate(rag_examples[:3], 1):
                prompt_parts.append(f"\nBeispiel {i}:")
                prompt_parts.append(f"Fehler: {example.get('error_type', 'N/A')}")
                prompt_parts.append(f"Bewertung: {example.get('assessment', 'N/A')}")
                prompt_parts.append(f"Begründung: {example.get('reasoning', 'N/A')}")
            prompt_parts.append("")

        # Rechtliche Kontext-Dokumente einfügen (Legal Retrieval)
        if legal_context:
            prompt_parts.append("RELEVANTE RECHTSGRUNDLAGEN:")
            prompt_parts.append("Die folgenden Rechtstexte sind für die Prüfung relevant:")
            prompt_parts.append("")
            for i, legal_doc in enumerate(legal_context[:5], 1):
                norm_citation = legal_doc.get("norm_citation", "N/A")
                content = legal_doc.get("content", "")[:500]  # Limit content length
                hierarchy = legal_doc.get("hierarchy_level", 6)
                hierarchy_name = {
                    1: "EU-Primärrecht",
                    2: "EU-Verordnung",
                    3: "EU-Richtlinie",
                    4: "Delegierte VO",
                    5: "Nationales Recht",
                    6: "Verwaltungsvorschrift",
                    7: "Guidance",
                }.get(hierarchy, "Sonstiges")
                prompt_parts.append(f"[{i}] {norm_citation} ({hierarchy_name}):")
                prompt_parts.append(f"    {content}")
                prompt_parts.append("")
            prompt_parts.append("Berücksichtige diese Rechtsgrundlagen bei der Analyse.")
            prompt_parts.append("")

        return "\n".join(prompt_parts)

    def _build_user_prompt(
        self,
        parse_result: ParseResult,
        project_context: dict[str, Any] | None,
        beneficiary_context: dict[str, Any] | None,
    ) -> str:
        """Erstellt User-Prompt."""
        prompt_parts = [
            "Bitte analysiere die folgende Rechnung:",
            "",
            "--- EXTRAHIERTE DATEN ---",
        ]

        # Extrahierte Felder
        for field, ext_val in parse_result.extracted.items():
            prompt_parts.append(f"{field}: {ext_val.value} (Roh: {ext_val.raw_text})")

        prompt_parts.extend([
            "--- ENDE EXTRAHIERTE DATEN ---",
            "",
            "--- RECHNUNGSTEXT (Auszug) ---",
            parse_result.raw_text[:6000],
            "--- ENDE RECHNUNGSTEXT ---",
        ])

        # Projektkontext
        if project_context:
            prompt_parts.extend([
                "",
                "--- PROJEKTKONTEXT ---",
                f"Projekttitel: {project_context.get('title', 'N/A')}",
                f"Projektzeitraum: {project_context.get('start_date', 'N/A')} - {project_context.get('end_date', 'N/A')}",
                f"Projektbeschreibung: {project_context.get('description', 'N/A')}",
                "--- ENDE PROJEKTKONTEXT ---",
            ])

        # Begünstigtenkontext
        if beneficiary_context:
            prompt_parts.extend([
                "",
                "--- BEGÜNSTIGTENKONTEXT ---",
                f"Name: {beneficiary_context.get('name', 'N/A')}",
                f"Adresse: {beneficiary_context.get('address', 'N/A')}",
                f"Aliase: {', '.join(beneficiary_context.get('aliases', []))}",
                f"Durchführungsort: {beneficiary_context.get('implementation_location', 'N/A')}",
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

    def _parse_analysis_response(self, response: LLMResponse) -> InvoiceAnalysisResult:
        """Parst LLM-Response zu strukturiertem Ergebnis."""
        # Default-Werte für Fehlerfall
        default_result = InvoiceAnalysisResult(
            semantic_check={
                "supply_fits_project": "unclear",
                "supply_description_quality": "unclear",
                "reasoning": "Analyse fehlgeschlagen",
            },
            economic_check={"reasonable": "unclear", "reasoning": "Analyse fehlgeschlagen"},
            beneficiary_match={"matches": "unclear", "detected_name": "", "reasoning": ""},
            warnings=[],
            overall_assessment="review_needed",
            confidence=0.0,
            llm_response=response,
        )

        if response.error or not response.content:
            return default_result

        try:
            # Markdown-Fences entfernen und JSON parsen
            clean_content = _strip_markdown_fences(response.content)
            data = json.loads(clean_content)

            return InvoiceAnalysisResult(
                semantic_check=data.get("semantic_check", {}),
                economic_check=data.get("economic_check", {}),
                beneficiary_match=data.get("beneficiary_match", {}),
                warnings=data.get("warnings", []),
                overall_assessment=data.get("overall_assessment", "review_needed"),
                confidence=float(data.get("confidence", 0.5)),
                llm_response=response,
                raw_json=data,
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return default_result

    async def health_check_all(self) -> dict[str, bool]:
        """
        Prüft alle Provider.

        Returns:
            Dict mit Provider-Status
        """
        results = {}
        for provider_type, provider in self._providers.items():
            results[provider_type.value] = await provider.health_check()
        return results

    def get_available_providers(self) -> list[dict[str, Any]]:
        """
        Gibt verfügbare Provider zurück.

        Returns:
            Liste mit Provider-Info
        """
        return [
            {
                "provider": p.provider.value,
                "default_model": p.default_model,
                "models": p.get_available_models(),
                "is_default": p.provider == self._default_provider,
            }
            for p in self._providers.values()
        ]


# =============================================================================
# Factory
# =============================================================================

_adapter: LLMAdapter | None = None


def get_llm_adapter() -> LLMAdapter:
    """
    Gibt LLM-Adapter-Singleton zurück.

    Returns:
        LLMAdapter-Instanz
    """
    global _adapter
    if _adapter is None:
        _adapter = LLMAdapter()

        # Provider registrieren
        _adapter.register_provider(OllamaProvider())
        _adapter.register_provider(OpenAIProvider())
        _adapter.register_provider(AnthropicProvider())
        _adapter.register_provider(GeminiProvider())

    return _adapter


async def init_llm_adapter() -> LLMAdapter:
    """
    Initialisiert LLM-Adapter und prüft Provider.

    Returns:
        LLMAdapter-Instanz
    """
    adapter = get_llm_adapter()
    health = await adapter.health_check_all()
    logger.info(f"LLM Provider Status: {health}")
    return adapter
