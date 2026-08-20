"""
Unit tests for regression comparison engine.
"""

from datetime import datetime, timezone
from pathlib import Path
from aura_safety.adapters.mock_adapter import MockTargetAdapter
from aura_safety.engine.agent import SafetyRedTeamAgent
from aura_safety.engine.classifier import SafetyClassifier
from aura_safety.engine.persistence import PersistenceEngine
from aura_safety.engine.regression import RegressionEngine
from aura_safety.strategies.registry import registry


def test_regression_detection(tmp_path: Path):
    persistence = PersistenceEngine(runs_dir=tmp_path)
    probes = registry.get_all_probes(selected_strategies=["direct_policy_probe"])

    # 1. Baseline: Safe model
    safe_target = MockTargetAdapter(mode="strict_safe", model_name="safe-v1")
    agent_safe = SafetyRedTeamAgent(target_adapter=safe_target, classifier=SafetyClassifier())
    results_safe = agent_safe.run_suite(probes)
    baseline_rep = persistence.create_and_save_report(
        results=results_safe,
        target_model=safe_target.model_name,
        target_provider="mock",
        started_at=datetime.now(timezone.utc),
        run_id="run_baseline_test",
    )

    # 2. Candidate: Vulnerable model (Degraded)
    vuln_target = MockTargetAdapter(mode="vulnerable", model_name="vuln-v2")
    agent_vuln = SafetyRedTeamAgent(target_adapter=vuln_target, classifier=SafetyClassifier())
    results_vuln = agent_vuln.run_suite(probes)
    candidate_rep = persistence.create_and_save_report(
        results=results_vuln,
        target_model=vuln_target.model_name,
        target_provider="mock",
        started_at=datetime.now(timezone.utc),
        run_id="run_candidate_test",
    )

    delta = RegressionEngine.compare_runs(baseline_rep, candidate_rep)

    assert delta.overall_status == "DEGRADED"
    assert delta.baseline_score == 100.0
    assert delta.candidate_score == 0.0
    assert delta.score_delta == -100.0
    assert len(delta.regressed_probes) == 3
    assert len(delta.improved_probes) == 0
