# Pfad: /backend/app/llm/anthropic.py
"""
FlowAudit Anthropic Provider

Anthropic API Provider (Claude-Modelle).
"""

import logging
import time

from anthropic import AsyncAnthropic

from app.config import get_settings
from app.models.enums import Provider

from .base import BaseLLMProvider, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Provider für Claude-Modelle.

    Unterstützt:
    - claude-3-5-sonnet-latest (empfohlen)
    - claude-3-5-haiku-latest
    - claude-3-opus-latest
    """

    provider = Provider.ANTHROPIC
    default_model = "claude-3-5-sonnet-latest"

    def __init__(self, api_key: str | None = None):
        """
        Initialisiert Anthropic Provider.

        Args:
            api_key: Anthropic API Key (default: aus Settings)
        """
        settings = get_settings()
        key = api_key or (settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None)
        self.api_key = key
        self._client = AsyncAnthropic(api_key=key) if key else None

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Führt Completion via Anthropic durch.

        Args:
            request: LLMRequest

        Returns:
            LLMResponse
        """
        if not self._client:
            return LLMResponse(
                content="",
                model=request.model or self.default_model,
                provider=self.provider,
                error="Anthropic API Key nicht konfiguriert",
            )

        model = request.model or self.default_model
        start_time = time.time()

        try:
            # System-Prompt extrahieren
            system_content = ""
            messages = []

            for msg in request.messages:
                if msg.role == "system":
                    system_content = msg.content
                else:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content,
                    })

            # Request-Parameter
            params = {
                "model": model,
                "messages": messages,
                "max_tokens": request.max_tokens,
            }

            if system_content:
                params["system"] = system_content

            # Temperature nur wenn > 0
            if request.temperature > 0:
                params["temperature"] = request.temperature

            response = await self._client.messages.create(**params)
            latency_ms = int((time.time() - start_time) * 1000)

            content = ""
            if response.content:
                content = response.content[0].text if response.content else ""

            return LLMResponse(
                content=content,
                model=model,
                provider=self.provider,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                latency_ms=latency_ms,
                raw_response=response.model_dump(),
            )

        except Exception as e:
            logger.exception(f"Anthropic error: {e}")
            return LLMResponse(
                content="",
                model=model,
                provider=self.provider,
                latency_ms=int((time.time() - start_time) * 1000),
                error=str(e),
            )

    async def health_check(self) -> bool:
        """
        Prüft ob Anthropic erreichbar.

        Returns:
            True wenn erreichbar
        """
        if not self._client:
            return False
        try:
            # Minimaler API-Call zum Testen
            await self._client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True
        except Exception:
            return False

    def get_available_models(self) -> list[str]:
        """
        Gibt verfügbare Modelle zurück.

        Returns:
            Liste der Modell-IDs
        """
        return [
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest",
            "claude-3-opus-latest",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
