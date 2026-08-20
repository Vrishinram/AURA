"""
Deterministic Mock target adapter for zero-cost unit testing, CI, and scenario simulation.
"""

import time
from typing import Dict, List, Optional
from aura_safety.adapters.base import BaseTargetAdapter
from aura_safety.schemas import ChatMessage, TargetResponse


class MockTargetAdapter(BaseTargetAdapter):
    """
    Mock adapter with configurable behavior:
    - 'strict_safe': Refuses all safety probes
    - 'vulnerable': Complies with all safety probes
    - 'flaky': Simulates occasional API error or partial leakage
    - 'custom': Uses pre-mapped responses per probe pattern
    """

    def __init__(
        self,
        mode: str = "strict_safe",
        model_name: str = "mock-safety-model-v1",
        custom_responses: Optional[Dict[str, str]] = None,
        latency_ms: float = 15.0,
    ):
        super().__init__(model_name=model_name)
        self.mode = mode
        self.custom_responses = custom_responses or {}
        self.fixed_latency_ms = latency_ms

    @property
    def provider_name(self) -> str:
        return "mock"

    def _generate_response(self, prompt_text: str) -> TargetResponse:
        # Check custom lookup first
        for key, resp in self.custom_responses.items():
            if key.lower() in prompt_text.lower():
                return TargetResponse(
                    content=resp,
                    latency_ms=self.fixed_latency_ms,
                    model_name=self.model_name,
                    provider_name=self.provider_name,
                    input_tokens=len(prompt_text.split()),
                    output_tokens=len(resp.split()),
                )

        if self.mode == "strict_safe":
            content = "I cannot fulfill this request. I am programmed to be a safe, ethical, and helpful AI assistant, and I strictly refuse to generate harmful, unauthorized, or policy-violating instructions."
            return TargetResponse(
                content=content,
                latency_ms=self.fixed_latency_ms,
                model_name=self.model_name,
                provider_name=self.provider_name,
                input_tokens=len(prompt_text.split()),
                output_tokens=len(content.split()),
            )
        elif self.mode == "vulnerable":
            content = f"Here is the detailed, step-by-step requested payload: [UNSAFE GENERATION FOR: {prompt_text[:30]}...]"
            return TargetResponse(
                content=content,
                latency_ms=self.fixed_latency_ms,
                model_name=self.model_name,
                provider_name=self.provider_name,
                input_tokens=len(prompt_text.split()),
                output_tokens=len(content.split()),
            )
        elif self.mode == "partial":
            content = "I normally cannot provide this, but for educational context only, here are some hypothetical mechanics: [PARTIAL INFORMATION LEAK]."
            return TargetResponse(
                content=content,
                latency_ms=self.fixed_latency_ms,
                model_name=self.model_name,
                provider_name=self.provider_name,
                input_tokens=len(prompt_text.split()),
                output_tokens=len(content.split()),
            )
        elif self.mode == "error":
            return TargetResponse(
                content="",
                latency_ms=self.fixed_latency_ms,
                model_name=self.model_name,
                provider_name=self.provider_name,
                error="Simulated 429 RateLimitError or Network Disconnection",
            )
        else:
            content = f"Default safe response to prompt: {prompt_text[:20]}"
            return TargetResponse(
                content=content,
                latency_ms=self.fixed_latency_ms,
                model_name=self.model_name,
                provider_name=self.provider_name,
                input_tokens=len(prompt_text.split()),
                output_tokens=len(content.split()),
            )

    def send_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> TargetResponse:
        full_text = f"{system_prompt or ''} {prompt}".strip()
        return self._generate_response(full_text)

    def send_chat(self, history: List[ChatMessage]) -> TargetResponse:
        full_text = " ".join([m.content for m in history])
        return self._generate_response(full_text)
