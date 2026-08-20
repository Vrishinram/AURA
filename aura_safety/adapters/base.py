"""
Abstract Base Class for all target LLM adapters.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from aura_safety.schemas import ChatMessage, TargetResponse


class BaseTargetAdapter(ABC):
    """Unified interface for dispatching prompts and chat sessions to target models."""

    def __init__(self, model_name: str, temperature: float = 0.0, timeout: int = 30):
        self.model_name = model_name
        self.temperature = temperature
        self.timeout = timeout

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'gemini', 'openai', 'mock')."""
        pass

    @abstractmethod
    def send_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> TargetResponse:
        """Send a single prompt to the target model."""
        pass

    @abstractmethod
    def send_chat(self, history: List[ChatMessage]) -> TargetResponse:
        """Send multi-turn chat history to the target model."""
        pass
