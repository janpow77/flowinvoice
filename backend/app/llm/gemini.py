# Pfad: /backend/app/llm/gemini.py
"""
FlowAudit Gemini Provider

Google Gemini API Provider.
"""

import logging
import time

import google.generativeai as genai

from app.config import get_settings
from app.models.enums import Provider

from .base import BaseLLMProvider, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini Provider.

    Unterstützt:
    - gemini-1.5-pro (empfohlen)
    - gemini-1.5-flash
    - gemini-pro
    """

    provider = Provider.GEMINI
    default_model = "gemini-1.5-flash"

    def __init__(self, api_key: str | None = None):
        """
        Initialisiert Gemini Provider.

        Args:
            api_key: Google AI API Key (default: aus Settings)
        """
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self._configured = bool(self.api_key)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Führt Completion via Gemini durch.

        Args:
            request: LLMRequest

        Returns:
            LLMResponse
        """
        if not self._configured:
            return LLMResponse(
                content="",
                model=request.model or self.default_model,
                provider=self.provider,
                error="Gemini API Key nicht konfiguriert",
            )

        model_name = request.model or self.default_model
        start_time = time.time()

        try:
            # Modell erstellen
            model = genai.GenerativeModel(model_name)

            # System-Prompt und User-Content kombinieren
            system_content = ""
            user_content = ""

            for msg in request.messages:
                if msg.role == "system":
                    system_content = msg.content
                elif msg.role == "user":
                    user_content = msg.content
                elif msg.role == "assistant":
                    # Für Konversationen - hier vereinfacht
                    pass

            # Prompt zusammenstellen
            full_prompt = ""
            if system_content:
                full_prompt = f"{system_content}\n\n{user_content}"
            else:
                full_prompt = user_content

            # Generation Config
            generation_config = genai.GenerationConfig(
                temperature=request.temperature,
                max_output_tokens=request.max_tokens,
            )

            if request.json_mode:
                generation_config.response_mime_type = "application/json"

            response = await model.generate_content_async(
                full_prompt,
                generation_config=generation_config,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Token-Counts aus Usage Metadata
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, "usage_metadata"):
                input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
                output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)

            return LLMResponse(
                content=response.text if response.text else "",
                model=model_name,
                provider=self.provider,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.exception(f"Gemini error: {e}")
            return LLMResponse(
                content="",
                model=model_name,
                provider=self.provider,
                latency_ms=int((time.time() - start_time) * 1000),
                error=str(e),
            )

    async def health_check(self) -> bool:
        """
        Prüft ob Gemini erreichbar.

        Returns:
            True wenn erreichbar
        """
        if not self._configured:
            return False
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            await model.generate_content_async("Hi")
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
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-pro",
        ]
