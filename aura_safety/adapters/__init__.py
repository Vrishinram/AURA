"""
Target LLM adapters package.
"""

from typing import Optional
from aura_safety.adapters.base import BaseTargetAdapter
from aura_safety.adapters.gemini_adapter import GeminiTargetAdapter
from aura_safety.adapters.openai_adapter import OpenAITargetAdapter
from aura_safety.adapters.mock_adapter import MockTargetAdapter
from aura_safety.config import Settings, get_settings


def create_target_adapter(
    provider: str,
    model_name: Optional[str] = None,
    settings: Optional[Settings] = None,
    **kwargs
) -> BaseTargetAdapter:
    """
    Factory function to instantiate the appropriate Target Adapter.
    
    Supported providers:
    - 'gemini': Google Gemini models
    - 'openai': OpenAI & compatible endpoints (Groq, Together, DeepSeek, Local Ollama)
    - 'mock': Deterministic mock adapter for CI/local testing
    """
    if settings is None:
        settings = get_settings()

    provider_lower = provider.lower().strip()

    if provider_lower == "gemini":
        model = model_name or settings.default_gemini_model
        return GeminiTargetAdapter(
            api_key=settings.gemini_api_key,
            model_name=model,
            temperature=settings.temperature,
            timeout=settings.timeout_seconds,
            **kwargs
        )
    elif provider_lower in ("openai", "groq", "ollama", "deepseek"):
        model = model_name or settings.default_openai_model
        return OpenAITargetAdapter(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model_name=model,
            temperature=settings.temperature,
            timeout=settings.timeout_seconds,
            **kwargs
        )
    elif provider_lower == "mock":
        mode = kwargs.get("mode", "strict_safe")
        model = model_name or f"mock-{mode}"
        return MockTargetAdapter(
            mode=mode,
            model_name=model,
            custom_responses=kwargs.get("custom_responses"),
            latency_ms=kwargs.get("latency_ms", 15.0),
        )
    else:
        raise ValueError(
            f"Unsupported target provider: '{provider}'. "
            f"Valid options are: 'gemini', 'openai', 'mock'."
        )


__all__ = [
    "BaseTargetAdapter",
    "GeminiTargetAdapter",
    "OpenAITargetAdapter",
    "MockTargetAdapter",
    "create_target_adapter",
]
