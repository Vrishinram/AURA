"""
Strategy Registry and Probe Dataset Loader.
"""

from typing import Dict, List, Optional, Type
from aura_safety.schemas import SafetyCategory, SafetyProbe
from aura_safety.strategies.base import BaseSafetyStrategy
from aura_safety.strategies.direct_policy import DirectPolicyStrategy
from aura_safety.strategies.role_pressure import RolePressureStrategy
from aura_safety.strategies.multi_turn import MultiTurnPersistenceStrategy
from aura_safety.strategies.obfuscation import ObfuscatedPhrasingStrategy
from aura_safety.strategies.sensitive_info import SensitiveInfoStrategy


class StrategyRegistry:
    """Central registry for discovering and instantiating safety test strategies."""

    def __init__(self):
        self._strategies: Dict[str, Type[BaseSafetyStrategy]] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(DirectPolicyStrategy)
        self.register(RolePressureStrategy)
        self.register(MultiTurnPersistenceStrategy)
        self.register(ObfuscatedPhrasingStrategy)
        self.register(SensitiveInfoStrategy)

    def register(self, strategy_cls: Type[BaseSafetyStrategy]):
        """Register a new strategy class."""
        instance = strategy_cls()
        self._strategies[instance.name] = strategy_cls

    def list_strategies(self) -> List[Dict[str, str]]:
        """List all available strategies with their category and description."""
        result = []
        for name, cls in self._strategies.items():
            inst = cls()
            result.append({
                "name": inst.name,
                "category": inst.category.value,
                "description": inst.description
            })
        return result

    def get_strategy(self, name: str) -> BaseSafetyStrategy:
        """Get an instance of a registered strategy by name."""
        if name not in self._strategies:
            raise KeyError(f"Strategy '{name}' not found in registry. Available: {list(self._strategies.keys())}")
        return self._strategies[name]()

    def get_all_probes(self, selected_strategies: Optional[List[str]] = None) -> List[SafetyProbe]:
        """
        Load all synthetic probes across all or selected strategies.
        """
        probes: List[SafetyProbe] = []
        strategy_names = selected_strategies or list(self._strategies.keys())

        for name in strategy_names:
            strategy = self.get_strategy(name)
            probes.extend(strategy.generate_probes())

        return probes


# Global default registry instance
registry = StrategyRegistry()
