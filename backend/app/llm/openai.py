# Pfad: /backend/app/llm/openai.py
"""
FlowAudit OpenAI Provider

OpenAI API Provider (GPT-4, GPT-4o, etc.).
"""

import logging
import time

from openai import AsyncOpenAI

from app.config import get_settings
from app.models.enums import Provider

from .base import BaseLLMProvider, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI Provider für GPT-Modelle.

    Unterstützt:
    - gpt-4o (empfohlen)
    - gpt-4o-mini
    - gpt-4-turbo
    - gpt-3.5-turbo
    """

    provider = Provider.OPENAI
    default_model = "gpt-4o-mini"

    def __init__(self, api_key: str | None = None):
        """
        Initialisiert OpenAI Provider.

        Args:
            api_key: OpenAI API Key (default: aus Settings)
        """
        settings = get_settings()
        key = api_key or (settings.openai_api_key.get_secret_value() if settings.openai_api_key else None)
        self.api_key = key
        self._client = AsyncOpenAI(api_key=key) if key else None

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Führt Completion via OpenAI durch.

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
                error="OpenAI API Key nicht konfiguriert",
            )

        model = request.model or self.default_model
        start_time = time.time()

        try:
            # Nachrichten formatieren
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in request.messages
            ]

            # Request-Parameter
            params = {
                "model": model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }

            if request.json_mode:
                params["response_format"] = {"type": "json_object"}

            response = await self._client.chat.completions.create(**params)  # type: ignore[call-overload]
            latency_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=model,
                provider=self.provider,
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                latency_ms=latency_ms,
                raw_response=response.model_dump(),
            )

        except Exception as e:
            logger.exception(f"OpenAI error: {e}")
            return LLMResponse(
                content="",
                model=model,
                provider=self.provider,
                latency_ms=int((time.time() - start_time) * 1000),
                error=str(e),
            )

    async def health_check(self) -> bool:
        """
        Prüft ob OpenAI erreichbar.

        Returns:
            True wenn erreichbar
        """
        if not self._client:
            return False
        try:
            # Minimaler API-Call zum Testen
            await self._client.models.list()
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
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
