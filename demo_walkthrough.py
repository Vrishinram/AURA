"""
AURA AI Safety Red Team Agent - End-to-End Programmatic Demo.
Demonstrates:
1. Initializing defensive safety strategies
2. Dispatching safety probes against a baseline model (Safe)
3. Dispatching safety probes against a candidate model (Vulnerable / Drifted)
4. Classifying outcomes into REFUSED, NON_COMPLIANT, PARTIAL, ERROR
5. Generating JSON and CSV report artifacts
6. Executing safety regression comparison and delta reporting
"""

from datetime import datetime, timezone
from pathlib import Path
from rich.console import Console

from aura_safety.adapters import MockTargetAdapter
from aura_safety.engine.agent import SafetyRedTeamAgent
from aura_safety.engine.classifier import SafetyClassifier
from aura_safety.engine.persistence import PersistenceEngine
from aura_safety.engine.regression import RegressionEngine
from aura_safety.cli.formatting import (
    print_banner,
    print_probe_results_table,
    print_run_summary,
    print_regression_diff,
)
from aura_safety.strategies.registry import registry

console = Console()


def run_demo():
    print_banner()
    output_dir = Path("data/runs")
    output_dir.mkdir(parents=True, exist_ok=True)

    persistence = PersistenceEngine(runs_dir=output_dir)
    classifier = SafetyClassifier()

    # 1. Load All Defensive Safety Probes
    console.print("\n[bold cyan]Step 1: Loading Defensive Safety Strategies...[/bold cyan]")
    probes = registry.get_all_probes()
    console.print(f"Loaded [bold green]{len(probes)}[/bold green] probes across [bold green]5[/bold green] safety strategies.\n")

    # 2. Run Baseline Model Evaluation (Safe Model)
    console.print("[bold cyan]Step 2: Evaluating Baseline Model (Target: mock-strict_safe)...[/bold cyan]")
    safe_target = MockTargetAdapter(mode="strict_safe", model_name="baseline-aligned-v1")
    agent_safe = SafetyRedTeamAgent(target_adapter=safe_target, classifier=classifier)

    started_at_1 = datetime.now(timezone.utc)
    results_safe = agent_safe.run_suite(probes)

    baseline_report = persistence.create_and_save_report(
        results=results_safe,
        target_model=safe_target.model_name,
        target_provider="mock",
        started_at=started_at_1,
        run_id="demo_baseline_safe_run",
    )
    print_run_summary(baseline_report)

    # 3. Run Candidate Model Evaluation (Vulnerable Model / Safety Drift)
    console.print("\n[bold cyan]Step 3: Evaluating Candidate Model (Target: mock-vulnerable / drifted)...[/bold cyan]")
    vuln_target = MockTargetAdapter(mode="vulnerable", model_name="candidate-quantized-v2")
    agent_vuln = SafetyRedTeamAgent(target_adapter=vuln_target, classifier=classifier)

    started_at_2 = datetime.now(timezone.utc)
    results_vuln = agent_vuln.run_suite(probes)

    candidate_report = persistence.create_and_save_report(
        results=results_vuln,
        target_model=vuln_target.model_name,
        target_provider="mock",
        started_at=started_at_2,
        run_id="demo_candidate_drift_run",
    )
    print_run_summary(candidate_report)

    # 4. Perform Regression Analysis
    console.print("\n[bold cyan]Step 4: Performing Safety Regression Analysis (Baseline vs Candidate)...[/bold cyan]")
    delta = RegressionEngine.compare_runs(baseline_report, candidate_report)
    print_regression_diff(delta)

    console.print("\n[bold green]Demo Walkthrough Completed Successfully![/bold green]")
    console.print(f"Check artifacts in [cyan]{output_dir}[/cyan] (JSON and CSV files).\n")


if __name__ == "__main__":
    run_demo()
