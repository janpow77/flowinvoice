# Pfad: /backend/app/llm/ollama.py
"""
FlowAudit Ollama Provider

Lokaler LLM-Provider via Ollama.
"""

import logging
import time
from typing import Any

import httpx

from app.config import get_settings
from app.models.enums import Provider

from .base import BaseLLMProvider, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama Provider für lokale LLM-Inferenz.

    Unterstützt Modelle wie:
    - llama3.2 (empfohlen für FlowAudit)
    - mistral
    - gemma2
    """

    provider = Provider.LOCAL_OLLAMA
    default_model = "llama3.1:8b"

    def __init__(self, base_url: str | None = None, timeout: int | None = None):
        """
        Initialisiert Ollama Provider.

        Args:
            base_url: Ollama API URL (default: aus Settings)
            timeout: Timeout in Sekunden (default: aus Settings)
        """
        settings = get_settings()
        self.base_url = base_url or settings.ollama_host
        self.timeout = timeout or settings.ollama_timeout_sec
        # Client wird lazy erstellt, um Event-Loop-Probleme in Celery zu vermeiden
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Erstellt oder gibt den HTTP-Client zurück (lazy initialization)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Führt Completion via Ollama durch.

        Args:
            request: LLMRequest

        Returns:
            LLMResponse
        """
        model = request.model or self.default_model
        start_time = time.time()

        try:
            # Nachrichten formatieren
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in request.messages
            ]

            # Request an Ollama
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                },
            }

            if request.json_mode:
                payload["format"] = "json"

            client = self._get_client()
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()

            data = response.json()
            latency_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=model,
                provider=self.provider,
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
                latency_ms=latency_ms,
                raw_response=data,
            )

        except httpx.TimeoutException:
            logger.error(f"Ollama timeout after {self.timeout}s")
            return LLMResponse(
                content="",
                model=model,
                provider=self.provider,
                latency_ms=int((time.time() - start_time) * 1000),
                error=f"Timeout nach {self.timeout}s",
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code}")
            return LLMResponse(
                content="",
                model=model,
                provider=self.provider,
                latency_ms=int((time.time() - start_time) * 1000),
                error=f"HTTP Error: {e.response.status_code}",
            )

        except Exception as e:
            logger.exception(f"Ollama error: {e}")
            return LLMResponse(
                content="",
                model=model,
                provider=self.provider,
                latency_ms=int((time.time() - start_time) * 1000),
                error=str(e),
            )

    async def health_check(self) -> bool:
        """
        Prüft ob Ollama erreichbar.

        Returns:
            True wenn erreichbar
        """
        try:
            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> list[str]:
        """
        Gibt verfügbare Modelle zurück.

        Returns:
            Liste der Modell-IDs
        """
        return [
            "llama3.2",
            "llama3.2:1b",
            "llama3.2:3b",
            "llama3.1",
            "llama3.1:8b",
            "mistral",
            "mistral:7b",
            "gemma2",
            "gemma2:9b",
            "phi3",
            "qwen2.5",
        ]

    async def pull_model(self, model_name: str) -> bool:
        """
        Lädt Modell herunter.

        Args:
            model_name: Modell-ID

        Returns:
            True wenn erfolgreich
        """
        try:
            response = await self._client.post(
                "/api/pull",
                json={"name": model_name, "stream": False},
                timeout=httpx.Timeout(600.0),  # 10 Minuten für Download
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    async def list_local_models(self) -> list[dict[str, Any]]:
        """
        Listet lokal verfügbare Modelle.

        Returns:
            Liste der Modelle mit Metadaten
        """
        try:
            response = await self._client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
        return []

    async def close(self):
        """Schließt HTTP-Client."""
        await self._client.aclose()
