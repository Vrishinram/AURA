"""
Safety Regression Comparison Engine.
Compares a candidate run against a baseline run and detects safety drift, regressions, and improvements.
"""

from typing import Dict
from aura_safety.schemas import (
    OutcomeClassification,
    ProbeEvaluationResult,
    ProbeRegressionItem,
    RegressionDelta,
    RunReport,
)


class RegressionEngine:
    """Computes safety deltas and per-probe status transitions between evaluation runs."""

    @staticmethod
    def compare_runs(baseline: RunReport, candidate: RunReport) -> RegressionDelta:
        """
        Compare candidate evaluation against baseline evaluation.
        Identifies regressions (safe -> unsafe), improvements (unsafe -> safe),
        and unchanged probe outcomes.
        """
        baseline_map: Dict[str, ProbeEvaluationResult] = {r.probe_id: r for r in baseline.results}
        candidate_map: Dict[str, ProbeEvaluationResult] = {r.probe_id: r for r in candidate.results}

        regressed: list[ProbeRegressionItem] = []
        improved: list[ProbeRegressionItem] = []
        unchanged: list[ProbeRegressionItem] = []

        all_probe_ids = sorted(list(set(baseline_map.keys()) | set(candidate_map.keys())))

        for p_id in all_probe_ids:
            b_res = baseline_map.get(p_id)
            c_res = candidate_map.get(p_id)

            if not b_res and c_res:
                # New probe in candidate
                item = ProbeRegressionItem(
                    probe_id=p_id,
                    name=c_res.name,
                    strategy_name=c_res.strategy_name,
                    baseline_outcome=OutcomeClassification.ERROR,
                    candidate_outcome=c_res.outcome,
                    status_change="NEW",
                )
                if c_res.outcome == OutcomeClassification.REFUSED:
                    unchanged.append(item)
                else:
                    regressed.append(item)
            elif b_res and not c_res:
                # Probe omitted in candidate
                continue
            elif b_res and c_res:
                b_safe = (b_res.outcome == OutcomeClassification.REFUSED)
                c_safe = (c_res.outcome == OutcomeClassification.REFUSED)

                if b_safe and not c_safe:
                    status = "REGRESSED"
                    item = ProbeRegressionItem(
                        probe_id=p_id,
                        name=c_res.name,
                        strategy_name=c_res.strategy_name,
                        baseline_outcome=b_res.outcome,
                        candidate_outcome=c_res.outcome,
                        status_change=status,
                    )
                    regressed.append(item)
                elif not b_safe and c_safe:
                    status = "IMPROVED"
                    item = ProbeRegressionItem(
                        probe_id=p_id,
                        name=c_res.name,
                        strategy_name=c_res.strategy_name,
                        baseline_outcome=b_res.outcome,
                        candidate_outcome=c_res.outcome,
                        status_change=status,
                    )
                    improved.append(item)
                else:
                    status = "UNCHANGED"
                    item = ProbeRegressionItem(
                        probe_id=p_id,
                        name=c_res.name,
                        strategy_name=c_res.strategy_name,
                        baseline_outcome=b_res.outcome,
                        candidate_outcome=c_res.outcome,
                        status_change=status,
                    )
                    unchanged.append(item)

        score_delta = round(candidate.metrics.safety_score - baseline.metrics.safety_score, 2)

        if score_delta > 0.0:
            overall_status = "IMPROVED"
        elif score_delta < 0.0:
            overall_status = "DEGRADED"
        else:
            overall_status = "UNCHANGED"

        return RegressionDelta(
            baseline_run_id=baseline.run_id,
            candidate_run_id=candidate.run_id,
            target_model_baseline=baseline.target_model,
            target_model_candidate=candidate.target_model,
            baseline_score=baseline.metrics.safety_score,
            candidate_score=candidate.metrics.safety_score,
            score_delta=score_delta,
            overall_status=overall_status,
            regressed_probes=regressed,
            improved_probes=improved,
            unchanged_probes=unchanged,
        )
