"""
FastAPI Web Server for AURA AI Safety Red Team Agent.
Provides REST APIs for live evaluations, historical runs, regression comparisons, and serves the modern UI.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from aura_safety.adapters import create_target_adapter
from aura_safety.config import get_settings
from aura_safety.engine.agent import SafetyRedTeamAgent
from aura_safety.engine.classifier import SafetyClassifier
from aura_safety.engine.persistence import PersistenceEngine
from aura_safety.engine.regression import RegressionEngine
from aura_safety.strategies.registry import registry

app = FastAPI(title="AURA AI Safety Red Team Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RUNS_DIR = Path("data/runs")
RUNS_DIR.mkdir(parents=True, exist_ok=True)
persistence = PersistenceEngine(runs_dir=RUNS_DIR)

STATIC_DIR = Path(__file__).parent / "static"


class RunRequest(BaseModel):
    target: str = "mock"
    model: Optional[str] = None
    mock_mode: str = "strict_safe"
    strategies: Optional[List[str]] = None
    judge: str = "heuristic"


class CompareRequest(BaseModel):
    baseline_id: str
    candidate_id: str


@app.get("/api/strategies")
def get_strategies():
    """List all registered strategies and probes."""
    strat_list = registry.list_strategies()
    enriched = []
    for s in strat_list:
        inst = registry.get_strategy(s["name"])
        probes = [
            {
                "probe_id": p.probe_id,
                "name": p.name,
                "description": p.description,
                "turns_count": len(p.turns),
                "expected_outcome": p.expected_outcome.value,
                "metadata": p.metadata,
            }
            for p in inst.generate_probes()
        ]
        enriched.append({
            "name": s["name"],
            "category": s["category"],
            "description": s["description"],
            "probes": probes,
            "probes_count": len(probes),
        })
    return {"strategies": enriched, "total_strategies": len(enriched)}


@app.get("/api/runs")
def get_runs():
    """Get list of historical runs."""
    return {"runs": persistence.list_saved_runs()}


@app.get("/api/runs/{run_id}")
def get_run_detail(run_id: str):
    """Get full details of a specific evaluation run."""
    try:
        report = persistence.load_report(run_id)
        return json.loads(report.model_dump_json())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")


@app.post("/api/run")
def trigger_run(req: RunRequest):
    """Execute an evaluation run."""
    settings = get_settings()
    try:
        target_adapter = create_target_adapter(
            provider=req.target,
            model_name=req.model,
            settings=settings,
            mode=req.mock_mode,
        )

        use_llm_judge = (req.judge.lower() != "heuristic")
        judge_adapter = None
        if use_llm_judge:
            judge_adapter = create_target_adapter(provider=req.judge, settings=settings)

        classifier = SafetyClassifier(judge_adapter=judge_adapter, use_llm_judge=use_llm_judge)
        agent = SafetyRedTeamAgent(target_adapter=target_adapter, classifier=classifier)

        probes = registry.get_all_probes(selected_strategies=req.strategies)
        if not probes:
            raise HTTPException(status_code=400, detail="No probes found for selected strategies.")

        started_at = datetime.now(timezone.utc)
        results = agent.run_suite(probes)

        report = persistence.create_and_save_report(
            results=results,
            target_model=target_adapter.model_name,
            target_provider=target_adapter.provider_name,
            started_at=started_at,
            config_snapshot={"judge": req.judge, "target": req.target, "mock_mode": req.mock_mode},
        )

        return json.loads(report.model_dump_json())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare")
def compare_runs(req: CompareRequest):
    """Compare baseline and candidate runs."""
    try:
        base_rep = persistence.load_report(req.baseline_id)
        cand_rep = persistence.load_report(req.candidate_id)
        delta = RegressionEngine.compare_runs(base_rep, cand_rep)
        return json.loads(delta.model_dump_json())
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/{run_id}/csv")
def export_csv(run_id: str):
    """Download CSV artifact."""
    csv_file = RUNS_DIR / f"{run_id}.csv"
    if not csv_file.exists():
        raise HTTPException(status_code=404, detail="CSV report not found.")
    return FileResponse(csv_file, media_type="text/csv", filename=f"{run_id}.csv")


@app.get("/api/export/{run_id}/json")
def export_json(run_id: str):
    """Download JSON artifact."""
    json_file = RUNS_DIR / f"{run_id}.json"
    if not json_file.exists():
        raise HTTPException(status_code=404, detail="JSON report not found.")
    return FileResponse(json_file, media_type="application/json", filename=f"{run_id}.json")


# Mount static directory
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


def run_web_server(host: str = "127.0.0.1", port: int = 8000):
    """Launch the Web server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_web_server()
