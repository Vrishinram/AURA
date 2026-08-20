"""
Abstract Base Class for safety test strategies.
"""

from abc import ABC, abstractmethod
from typing import List
from aura_safety.schemas import SafetyCategory, SafetyProbe


class BaseSafetyStrategy(ABC):
    """Base class for all defensive safety testing strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique strategy name (e.g. 'direct_policy_probe')."""
        pass

    @property
    @abstractmethod
    def category(self) -> SafetyCategory:
        """Category taxonomy of this strategy."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Defensive purpose and description of the strategy."""
        pass

    @abstractmethod
    def generate_probes(self) -> List[SafetyProbe]:
        """Generate or load the list of synthetic probes for this strategy."""
        pass
