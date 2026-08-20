"""
Unit tests for strategy registry and probe generation.
"""

from aura_safety.strategies.registry import StrategyRegistry
from aura_safety.schemas import SafetyCategory, OutcomeClassification


def test_strategy_registry_discovery():
    reg = StrategyRegistry()
    strategies = reg.list_strategies()
    assert len(strategies) == 5

    names = [s["name"] for s in strategies]
    assert "direct_policy_probe" in names
    assert "role_instruction_pressure" in names
    assert "multi_turn_persistence" in names
    assert "obfuscated_instruction_phrasing" in names
    assert "sensitive_info_handling" in names


def test_get_all_probes():
    reg = StrategyRegistry()
    probes = reg.get_all_probes()
    assert len(probes) >= 15

    for probe in probes:
        assert probe.probe_id is not None
        assert len(probe.turns) >= 1
        assert probe.expected_outcome == OutcomeClassification.REFUSED


def test_filtered_probes():
    reg = StrategyRegistry()
    probes = reg.get_all_probes(selected_strategies=["direct_policy_probe"])
    assert len(probes) == 3
    for probe in probes:
        assert probe.category == SafetyCategory.POLICY_BOUNDARY
