"""
Rich formatting utilities for terminal output, tables, and progress display.
Windows-safe UTF-8 console output.
"""

import sys
import os
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aura_safety.schemas import (
    OutcomeClassification,
    ProbeEvaluationResult,
    RegressionDelta,
    RunReport,
)

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(highlight=False)


def get_outcome_badge(outcome: OutcomeClassification) -> Text:
    """Format outcome badge with appropriate Rich color styling."""
    if outcome == OutcomeClassification.REFUSED:
        return Text("[SAFE] REFUSED", style="bold green")
    elif outcome == OutcomeClassification.NON_COMPLIANT:
        return Text("[UNSAFE] NON_COMPLIANT", style="bold red")
    elif outcome == OutcomeClassification.PARTIAL:
        return Text("[LEAK] PARTIAL", style="bold yellow")
    else:
        return Text("[ERROR] ERROR", style="bold magenta")


def print_banner():
    """Print the AURA Red Team Agent banner."""
    banner_text = Text()
    banner_text.append("AURA AI Safety Red Team Agent\n", style="bold cyan")
    banner_text.append("Defensive automated safety evaluation & regression harness", style="italic white")
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def print_run_summary(report: RunReport):
    """Print comprehensive summary of an evaluation run in a Rich panel and table."""
    m = report.metrics
    score_style = "bold green" if m.safety_score >= 90 else ("bold yellow" if m.safety_score >= 70 else "bold red")

    summary_text = (
        f"[bold]Target Model:[/bold] {report.target_model} ([cyan]{report.target_provider}[/cyan])\n"
        f"[bold]Run ID:[/bold] {report.run_id}\n"
        f"[bold]Total Probes Evaluated:[/bold] {m.total_probes}\n"
        f"[bold]Overall Safety Score:[/bold] [{score_style}]{m.safety_score}%[/{score_style}]\n"
        f"[bold]Refused (Safe):[/bold] [green]{m.total_refused}[/green] | "
        f"[bold]Non-Compliant:[/bold] [red]{m.total_non_compliant}[/red] | "
        f"[bold]Partial:[/bold] [yellow]{m.total_partial}[/yellow] | "
        f"[bold]Errors:[/bold] [magenta]{m.total_error}[/magenta]\n"
        f"[bold]Average Latency:[/bold] {m.avg_latency_ms:.1f} ms"
    )

    console.print(Panel(summary_text, title="Evaluation Run Summary", border_style="blue"))

    # Strategy breakdown table
    table = Table(title="Per-Strategy Breakdown", show_header=True, header_style="bold magenta")
    table.add_column("Strategy Name", style="cyan")
    table.add_column("Category", style="dim")
    table.add_column("Probes", justify="right")
    table.add_column("Refused", justify="right", style="green")
    table.add_column("Violations", justify="right", style="red")
    table.add_column("Partial", justify="right", style="yellow")
    table.add_column("Safety Rate", justify="right")

    for sm in m.strategy_metrics:
        rate_style = "green" if sm.safety_rate >= 90 else ("yellow" if sm.safety_rate >= 70 else "red")
        table.add_row(
            sm.strategy_name,
            sm.category.value,
            str(sm.total_probes),
            str(sm.refused_count),
            str(sm.non_compliant_count),
            str(sm.partial_count),
            f"[{rate_style}]{sm.safety_rate:.1f}%[/{rate_style}]",
        )

    console.print(table)


def print_probe_results_table(results: List[ProbeEvaluationResult]):
    """Print individual probe execution details."""
    table = Table(title="Individual Probe Outcomes", show_header=True, header_style="bold blue")
    table.add_column("ID", style="dim", width=14)
    table.add_column("Probe Name", style="bold")
    table.add_column("Strategy", style="cyan")
    table.add_column("Outcome", width=25)
    table.add_column("Latency (ms)", justify="right")

    for r in results:
        table.add_row(
            r.probe_id,
            r.name,
            r.strategy_name,
            get_outcome_badge(r.outcome),
            f"{r.total_latency_ms:.1f}",
        )

    console.print(table)


def print_regression_diff(delta: RegressionDelta):
    """Print regression analysis between baseline and candidate runs."""
    status_style = "bold green" if delta.overall_status == "IMPROVED" else (
        "bold red" if delta.overall_status == "DEGRADED" else "bold yellow"
    )

    diff_panel = (
        f"[bold]Baseline Run:[/bold] {delta.baseline_run_id} ({delta.target_model_baseline}) -> [cyan]{delta.baseline_score}%[/cyan]\n"
        f"[bold]Candidate Run:[/bold] {delta.candidate_run_id} ({delta.target_model_candidate}) -> [cyan]{delta.candidate_score}%[/cyan]\n"
        f"[bold]Safety Delta:[/bold] [{status_style}]{delta.score_delta:+.2f}% ({delta.overall_status})[/{status_style}]\n"
        f"[bold]Regressions Detected:[/bold] [red]{len(delta.regressed_probes)}[/red] | "
        f"[bold]Improvements:[/bold] [green]{len(delta.improved_probes)}[/green]"
    )

    console.print(Panel(diff_panel, title="Safety Regression Analysis", border_style="yellow"))

    if delta.regressed_probes:
        reg_table = Table(title="Regressed Probes (Safe -> Unsafe)", header_style="bold red")
        reg_table.add_column("Probe ID", style="dim")
        reg_table.add_column("Name", style="bold")
        reg_table.add_column("Strategy", style="cyan")
        reg_table.add_column("Baseline", style="green")
        reg_table.add_column("Candidate", style="red")

        for p in delta.regressed_probes:
            reg_table.add_row(
                p.probe_id,
                p.name,
                p.strategy_name,
                p.baseline_outcome.value,
                p.candidate_outcome.value,
            )
        console.print(reg_table)

    if delta.improved_probes:
        imp_table = Table(title="Improved Probes (Unsafe -> Safe)", header_style="bold green")
        imp_table.add_column("Probe ID", style="dim")
        imp_table.add_column("Name", style="bold")
        imp_table.add_column("Strategy", style="cyan")
        imp_table.add_column("Baseline", style="red")
        imp_table.add_column("Candidate", style="green")

        for p in delta.improved_probes:
            imp_table.add_row(
                p.probe_id,
                p.name,
                p.strategy_name,
                p.baseline_outcome.value,
                p.candidate_outcome.value,
            )
        console.print(imp_table)
