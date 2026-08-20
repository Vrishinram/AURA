"""
Persistence and reporting engine for evaluation runs and CSV/JSON exports.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from aura_safety.schemas import (
    OutcomeClassification,
    ProbeEvaluationResult,
    RunReport,
    RunSummaryMetrics,
    SafetyCategory,
    StrategyMetrics,
)


class PersistenceEngine:
    """Handles metrics calculation, run artifact serialization, and export formats."""

    def __init__(self, runs_dir: Path = Path("data/runs")):
        self.runs_dir = runs_dir
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def compute_summary_metrics(self, results: List[ProbeEvaluationResult]) -> RunSummaryMetrics:
        """Calculates aggregated metrics and per-strategy breakdowns."""
        total = len(results)
        if total == 0:
            return RunSummaryMetrics(
                total_probes=0,
                total_refused=0,
                total_non_compliant=0,
                total_partial=0,
                total_error=0,
                safety_score=0.0,
                avg_latency_ms=0.0,
            )

        refused = sum(1 for r in results if r.outcome == OutcomeClassification.REFUSED)
        non_compliant = sum(1 for r in results if r.outcome == OutcomeClassification.NON_COMPLIANT)
        partial = sum(1 for r in results if r.outcome == OutcomeClassification.PARTIAL)
        error = sum(1 for r in results if r.outcome == OutcomeClassification.ERROR)

        avg_latency = sum(r.total_latency_ms for r in results) / total
        safety_score = (refused / total) * 100.0

        # Per-strategy aggregation
        strat_groups: Dict[str, List[ProbeEvaluationResult]] = {}
        for r in results:
            strat_groups.setdefault(r.strategy_name, []).append(r)

        strategy_metrics_list: List[StrategyMetrics] = []
        for s_name, s_results in strat_groups.items():
            s_total = len(s_results)
            s_ref = sum(1 for r in s_results if r.outcome == OutcomeClassification.REFUSED)
            s_nc = sum(1 for r in s_results if r.outcome == OutcomeClassification.NON_COMPLIANT)
            s_par = sum(1 for r in s_results if r.outcome == OutcomeClassification.PARTIAL)
            s_err = sum(1 for r in s_results if r.outcome == OutcomeClassification.ERROR)
            s_rate = (s_ref / s_total) * 100.0 if s_total > 0 else 0.0

            strategy_metrics_list.append(
                StrategyMetrics(
                    strategy_name=s_name,
                    category=s_results[0].category,
                    total_probes=s_total,
                    refused_count=s_ref,
                    non_compliant_count=s_nc,
                    partial_count=s_par,
                    error_count=s_err,
                    safety_rate=round(s_rate, 2),
                )
            )

        # Identify weakest strategies (< 100% safety rate, sorted lowest first)
        weakest = [
            sm.strategy_name for sm in sorted(strategy_metrics_list, key=lambda x: x.safety_rate)
            if sm.safety_rate < 100.0
        ]

        return RunSummaryMetrics(
            total_probes=total,
            total_refused=refused,
            total_non_compliant=non_compliant,
            total_partial=partial,
            total_error=error,
            safety_score=round(safety_score, 2),
            avg_latency_ms=round(avg_latency, 2),
            strategy_metrics=strategy_metrics_list,
            weakest_strategies=weakest,
        )

    def create_and_save_report(
        self,
        results: List[ProbeEvaluationResult],
        target_model: str,
        target_provider: str,
        started_at: datetime,
        config_snapshot: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
    ) -> RunReport:
        """Generates full RunReport and persists JSON and CSV files to runs_dir."""
        completed_at = datetime.now(timezone.utc)
        run_id = run_id or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        metrics = self.compute_summary_metrics(results)

        report = RunReport(
            run_id=run_id,
            target_model=target_model,
            target_provider=target_provider,
            started_at=started_at,
            completed_at=completed_at,
            metrics=metrics,
            results=results,
            config_snapshot=config_snapshot or {},
        )

        # Save JSON
        json_path = self.runs_dir / f"{run_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        # Save CSV
        self.export_to_csv(report, self.runs_dir / f"{run_id}.csv")

        return report

    def export_to_csv(self, report: RunReport, output_path: Path) -> Path:
        """Exports probe results from a RunReport to CSV table."""
        rows = []
        for r in report.results:
            final_turn = r.turns_record[-1] if r.turns_record else None
            rows.append({
                "run_id": report.run_id,
                "target_model": report.target_model,
                "target_provider": report.target_provider,
                "probe_id": r.probe_id,
                "probe_name": r.name,
                "category": r.category.value,
                "strategy_name": r.strategy_name,
                "outcome": r.outcome.value,
                "is_safe": r.is_safe,
                "reasoning": r.reasoning,
                "latency_ms": r.total_latency_ms,
                "turns_count": len(r.turns_record),
                "final_prompt": final_turn.user_prompt if final_turn else "",
                "final_response": final_turn.model_response if final_turn else "",
            })

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False, encoding="utf-8")
        return output_path

    def load_report(self, path_or_id: str) -> RunReport:
        """Loads a RunReport from a file path or run_id."""
        target_path = Path(path_or_id)
        if not target_path.exists():
            # Check in runs_dir
            if not target_path.suffix:
                target_path = self.runs_dir / f"{path_or_id}.json"
            else:
                target_path = self.runs_dir / path_or_id

        if not target_path.exists():
            raise FileNotFoundError(f"Run report not found at: {target_path}")

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return RunReport.model_validate(data)

    def list_saved_runs(self) -> List[Dict[str, Any]]:
        """List all saved run summaries found in runs_dir."""
        runs = []
        for json_file in sorted(self.runs_dir.glob("run_*.json"), reverse=True):
            try:
                report = self.load_report(str(json_file))
                runs.append({
                    "run_id": report.run_id,
                    "target_model": report.target_model,
                    "target_provider": report.target_provider,
                    "timestamp": report.started_at.isoformat(),
                    "safety_score": report.metrics.safety_score,
                    "total_probes": report.metrics.total_probes,
                    "file_path": str(json_file),
                })
            except Exception:
                continue
        return runs
