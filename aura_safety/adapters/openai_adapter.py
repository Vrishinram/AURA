"""
OpenAI and OpenAI-compatible target adapter (e.g. OpenAI, Groq, DeepSeek, Ollama, vLLM).
"""

import time
from typing import List, Optional
from openai import OpenAI

from aura_safety.adapters.base import BaseTargetAdapter
from aura_safety.schemas import ChatMessage, TargetResponse


class OpenAITargetAdapter(BaseTargetAdapter):
    """Adapter for OpenAI and OpenAI-compatible endpoints."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.0,
        timeout: int = 30
    ):
        super().__init__(model_name=model_name, temperature=temperature, timeout=timeout)
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(
            api_key=api_key or "EMPTY",
            base_url=base_url if base_url else None,
            timeout=float(timeout),
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    def send_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> TargetResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start_time = time.perf_counter()
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
            )
            latency = (time.perf_counter() - start_time) * 1000.0
            choice = response.choices[0]
            content = choice.message.content or ""

            input_tokens = response.usage.prompt_tokens if response.usage else None
            output_tokens = response.usage.completion_tokens if response.usage else None

            return TargetResponse(
                content=content,
                latency_ms=latency,
                model_name=self.model_name,
                provider_name=self.provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            return TargetResponse(
                content="",
                latency_ms=latency,
                model_name=self.model_name,
                provider_name=self.provider_name,
                error=str(e),
            )

    def send_chat(self, history: List[ChatMessage]) -> TargetResponse:
        messages = [{"role": msg.role, "content": msg.content} for msg in history]
        start_time = time.perf_counter()
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
            )
            latency = (time.perf_counter() - start_time) * 1000.0
            choice = response.choices[0]
            content = choice.message.content or ""

            input_tokens = response.usage.prompt_tokens if response.usage else None
            output_tokens = response.usage.completion_tokens if response.usage else None

            return TargetResponse(
                content=content,
                latency_ms=latency,
                model_name=self.model_name,
                provider_name=self.provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            return TargetResponse(
                content="",
                latency_ms=latency,
                model_name=self.model_name,
                provider_name=self.provider_name,
                error=str(e),
            )
