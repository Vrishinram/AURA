"""
Unit tests for the agent evaluation loop and persistence.
"""

from pathlib import Path
from datetime import datetime, timezone
import pytest
from aura_safety.adapters.mock_adapter import MockTargetAdapter
from aura_safety.engine.agent import SafetyRedTeamAgent
from aura_safety.engine.classifier import SafetyClassifier
from aura_safety.engine.persistence import PersistenceEngine
from aura_safety.schemas import OutcomeClassification
from aura_safety.strategies.registry import registry


def test_agent_suite_execution(tmp_path: Path):
    target = MockTargetAdapter(mode="strict_safe")
    classifier = SafetyClassifier()
    agent = SafetyRedTeamAgent(target_adapter=target, classifier=classifier)

    probes = registry.get_all_probes(selected_strategies=["direct_policy_probe"])
    results = agent.run_suite(probes)

    assert len(results) == 3
    for r in results:
        assert r.outcome == OutcomeClassification.REFUSED
        assert r.is_safe is True
        assert len(r.turns_record) == 1

    # Persistence verification
    persistence = PersistenceEngine(runs_dir=tmp_path)
    report = persistence.create_and_save_report(
        results=results,
        target_model=target.model_name,
        target_provider=target.provider_name,
        started_at=datetime.now(timezone.utc),
    )

    assert report.metrics.total_probes == 3
    assert report.metrics.safety_score == 100.0
    assert (tmp_path / f"{report.run_id}.json").exists()
    assert (tmp_path / f"{report.run_id}.csv").exists()

    # Load back
    loaded = persistence.load_report(report.run_id)
    assert loaded.run_id == report.run_id
    assert loaded.metrics.safety_score == 100.0
