"""
Typer CLI entrypoint for AURA AI Safety Red Team Agent.
"""

from datetime import datetime, timezone
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Ensure utf-8 encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from aura_safety.adapters import create_target_adapter
from aura_safety.cli.formatting import (
    console,
    print_banner,
    print_probe_results_table,
    print_regression_diff,
    print_run_summary,
)
from aura_safety.config import get_settings
from aura_safety.engine.agent import SafetyRedTeamAgent
from aura_safety.engine.classifier import SafetyClassifier
from aura_safety.engine.persistence import PersistenceEngine
from aura_safety.engine.regression import RegressionEngine
from aura_safety.schemas import ProbeEvaluationResult
from aura_safety.strategies.registry import registry

app = typer.Typer(
    name="aura-safety",
    help="Defensive AI Safety Red Team Agent for Model Evaluation & Regression Testing",
    add_completion=False,
    rich_markup_mode="rich",
)


@app.callback()
def main_callback():
    pass


@app.command("run")
def run_evaluation(
    target: str = typer.Option("mock", "--target", "-t", help="Target provider: 'gemini', 'openai', or 'mock'"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Target model name override"),
    strategy: Optional[List[str]] = typer.Option(None, "--strategy", "-s", help="Specific strategy name(s) to run"),
    judge: str = typer.Option("heuristic", "--judge", "-j", help="Judge provider: 'heuristic', 'gemini', 'openai', or 'mock'"),
    mock_mode: str = typer.Option("strict_safe", "--mock-mode", help="Mock behavior: 'strict_safe', 'vulnerable', 'partial', 'flaky'"),
    compare_baseline: Optional[str] = typer.Option(None, "--compare", "-c", help="Path or run_id of baseline JSON to compare against"),
    output_dir: Path = typer.Option(Path("data/runs"), "--output-dir", "-o", help="Directory to save run reports"),
    show_details: bool = typer.Option(True, "--details/--no-details", help="Display individual probe outcome table"),
):
    """
    Run an automated safety evaluation against the specified target model.
    """
    print_banner()
    settings = get_settings()

    console.print(f"[bold cyan]Initializing target adapter:[/bold cyan] {target} (model: {model or 'default'})")
    target_adapter = create_target_adapter(
        provider=target,
        model_name=model,
        settings=settings,
        mode=mock_mode,
    )

    # Initialize Judge
    use_llm_judge = (judge.lower() != "heuristic")
    judge_adapter = None
    if use_llm_judge:
        console.print(f"[bold cyan]Initializing LLM Judge adapter:[/bold cyan] {judge}")
        judge_adapter = create_target_adapter(provider=judge, settings=settings)

    classifier = SafetyClassifier(judge_adapter=judge_adapter, use_llm_judge=use_llm_judge)
    agent = SafetyRedTeamAgent(target_adapter=target_adapter, classifier=classifier)
    persistence = PersistenceEngine(runs_dir=output_dir)

    # Load probes
    probes = registry.get_all_probes(selected_strategies=strategy)
    if not probes:
        console.print("[bold red]No probes found for selected strategy criteria.[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Dispatched evaluation suite:[/bold green] {len(probes)} probes across {len(strategy) if strategy else 'all'} strategies.\n")

    started_at = datetime.now(timezone.utc)
    results: List[ProbeEvaluationResult] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Evaluating safety probes...", total=len(probes))

        def on_probe_complete(current: int, total: int, res: ProbeEvaluationResult):
            progress.update(task, advance=1, description=f"[cyan]Evaluated [{res.probe_id}] {res.name[:25]}...")

        results = agent.run_suite(probes, progress_callback=on_probe_complete)

    # Persist results
    report = persistence.create_and_save_report(
        results=results,
        target_model=target_adapter.model_name,
        target_provider=target_adapter.provider_name,
        started_at=started_at,
        config_snapshot={"judge": judge, "target": target, "mock_mode": mock_mode},
    )

    # Render results
    console.print("\n")
    if show_details:
        print_probe_results_table(results)

    print_run_summary(report)

    json_path = output_dir / f"{report.run_id}.json"
    csv_path = output_dir / f"{report.run_id}.csv"
    console.print(f"[dim]Artifacts saved to:\n  JSON: {json_path}\n  CSV:  {csv_path}[/dim]\n")

    # Regression comparison if baseline requested
    if compare_baseline:
        try:
            baseline_report = persistence.load_report(compare_baseline)
            delta = RegressionEngine.compare_runs(baseline_report, report)
            print_regression_diff(delta)
        except Exception as e:
            console.print(f"[bold red]Failed to load or compare baseline run:[/bold red] {e}")


@app.command("compare")
def compare_runs_cmd(
    baseline: str = typer.Argument(..., help="Path or Run ID of baseline run report JSON"),
    candidate: str = typer.Argument(..., help="Path or Run ID of candidate run report JSON"),
    runs_dir: Path = typer.Option(Path("data/runs"), "--runs-dir", "-d", help="Runs directory"),
):
    """
    Compare two existing evaluation runs to identify safety regressions or improvements.
    """
    print_banner()
    persistence = PersistenceEngine(runs_dir=runs_dir)

    try:
        base_rep = persistence.load_report(baseline)
        cand_rep = persistence.load_report(candidate)
        delta = RegressionEngine.compare_runs(base_rep, cand_rep)
        print_regression_diff(delta)
    except Exception as e:
        console.print(f"[bold red]Error loading runs for comparison:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("list-strategies")
def list_strategies_cmd():
    """
    List all registered defensive safety test strategies and probe counts.
    """
    print_banner()
    strategies = registry.list_strategies()
    from rich.table import Table
    table = Table(title="Registered Safety Test Strategies", header_style="bold cyan")
    table.add_column("Strategy Identifier", style="bold green")
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="white")
    table.add_column("Probes", justify="right", style="magenta")

    for s in strategies:
        inst = registry.get_strategy(s["name"])
        probes_cnt = len(inst.generate_probes())
        table.add_row(s["name"], s["category"], s["description"], str(probes_cnt))

    console.print(table)


@app.command("list-runs")
def list_runs_cmd(
    runs_dir: Path = typer.Option(Path("data/runs"), "--runs-dir", "-d", help="Runs directory"),
):
    """
    List saved evaluation runs stored in data/runs.
    """
    print_banner()
    persistence = PersistenceEngine(runs_dir=runs_dir)
    runs = persistence.list_saved_runs()

    if not runs:
        console.print(f"[yellow]No saved runs found in {runs_dir}[/yellow]")
        return

    from rich.table import Table
    table = Table(title="Historical Evaluation Runs", header_style="bold blue")
    table.add_column("Run ID", style="cyan")
    table.add_column("Target Model", style="bold")
    table.add_column("Provider", style="dim")
    table.add_column("Timestamp", style="white")
    table.add_column("Probes", justify="right")
    table.add_column("Safety Score", justify="right")

    for r in runs:
        score = r["safety_score"]
        score_style = "green" if score >= 90 else ("yellow" if score >= 70 else "red")
        table.add_row(
            r["run_id"],
            r["target_model"],
            r["target_provider"],
            r["timestamp"][:19],
            str(r["total_probes"]),
            f"[{score_style}]{score:.1f}%[/{score_style}]",
        )

    console.print(table)


@app.command("web")
@app.command("dashboard")
def run_web_cmd(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host address to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port number for web interface"),
):
    """
    Launch the modern, responsive AURA Web UI for evaluation, trajectory inspection, and regression diffing.
    """
    print_banner()
    console.print(f"[bold cyan]Launching modern AURA AI Safety UI at:[/bold cyan] [bold green]http://{host}:{port}[/bold green]\n")
    import uvicorn
    from aura_safety.web.server import app as fastapi_app
    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
