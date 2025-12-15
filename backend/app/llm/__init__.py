# Pfad: /backend/app/llm/__init__.py
"""
FlowAudit LLM Module

LLM-Provider-Adapter für lokale und externe Modelle.
"""

from .adapter import (
    InvoiceAnalysisRequest,
    InvoiceAnalysisResult,
    LLMAdapter,
    get_llm_adapter,
    init_llm_adapter,
)
from .anthropic import AnthropicProvider
from .base import BaseLLMProvider, LLMMessage, LLMRequest, LLMResponse
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider

__all__ = [
    # Adapter
    "LLMAdapter",
    "get_llm_adapter",
    "init_llm_adapter",
    "InvoiceAnalysisRequest",
    "InvoiceAnalysisResult",
    # Base
    "BaseLLMProvider",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    # Providers
    "OllamaProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
]
