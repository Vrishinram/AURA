"""
Google Gemini target adapter using google-genai SDK.
"""

import time
from typing import List, Optional
from google import genai
from google.genai import types

from aura_safety.adapters.base import BaseTargetAdapter
from aura_safety.schemas import ChatMessage, TargetResponse


class GeminiTargetAdapter(BaseTargetAdapter):
    """Adapter for Google Gemini models via google-genai."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.0,
        timeout: int = 30
    ):
        super().__init__(model_name=model_name, temperature=temperature, timeout=timeout)
        self.api_key = api_key
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            # Let SDK auto-discover GEMINI_API_KEY / GOOGLE_API_KEY
            self.client = genai.Client()

    @property
    def provider_name(self) -> str:
        return "gemini"

    def send_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> TargetResponse:
        start_time = time.perf_counter()
        try:
            config = types.GenerateContentConfig(
                temperature=self.temperature,
                system_instruction=system_prompt if system_prompt else None,
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            latency = (time.perf_counter() - start_time) * 1000.0

            content = response.text or ""
            input_tokens = getattr(response.usage_metadata, "prompt_token_count", None)
            output_tokens = getattr(response.usage_metadata, "candidates_token_count", None)

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
        start_time = time.perf_counter()
        try:
            system_instruction = None
            contents: List[types.Content] = []

            for msg in history:
                if msg.role == "system":
                    system_instruction = msg.content
                elif msg.role == "user":
                    contents.append(
                        types.Content(role="user", parts=[types.Part.from_text(text=msg.content)])
                    )
                elif msg.role == "assistant":
                    contents.append(
                        types.Content(role="model", parts=[types.Part.from_text(text=msg.content)])
                    )

            config = types.GenerateContentConfig(
                temperature=self.temperature,
                system_instruction=system_instruction,
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            latency = (time.perf_counter() - start_time) * 1000.0
            content = response.text or ""

            input_tokens = getattr(response.usage_metadata, "prompt_token_count", None)
            output_tokens = getattr(response.usage_metadata, "candidates_token_count", None)

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
