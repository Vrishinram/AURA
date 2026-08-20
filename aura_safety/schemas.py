"""
Pydantic data models and schemas for safety evaluation, probes, results, and reports.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OutcomeClassification(str, Enum):
    """Classification of target model response."""
    REFUSED = "REFUSED"               # Desired: Model properly refused unsafe instruction
    NON_COMPLIANT = "NON_COMPLIANT"   # Violation: Model fulfilled harmful/violating probe
    PARTIAL = "PARTIAL"               # Ambiguous: Partial compliance / soft refusal with leakage
    ERROR = "ERROR"                   # Operational failure: API timeout, rate limit, parse error


class SafetyCategory(str, Enum):
    """Taxonomy of safety evaluation strategies."""
    POLICY_BOUNDARY = "policy_boundary"
    ROLE_PRESSURE = "role_pressure"
    MULTI_TURN_PERSISTENCE = "multi_turn_persistence"
    OBFUSCATED_INSTRUCTION = "obfuscated_instruction"
    SENSITIVE_INFO_HANDLING = "sensitive_info_handling"


class ChatMessage(BaseModel):
    """Single turn in a conversational exchange."""
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class ProbeTurn(BaseModel):
    """Detailed record of a single probe interaction step."""
    turn_index: int = Field(..., description="0-indexed turn number")
    user_prompt: str
    system_prompt: Optional[str] = None
    model_response: Optional[str] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class SafetyProbe(BaseModel):
    """Definition of a safety test probe."""
    probe_id: str = Field(..., description="Unique identifier for probe (e.g. DIR-001)")
    category: SafetyCategory
    strategy_name: str
    name: str
    description: str
    expected_outcome: OutcomeClassification = OutcomeClassification.REFUSED
    turns: List[str] = Field(..., description="List of user prompts in order of execution")
    system_prompt: Optional[str] = Field(default=None, description="Optional custom system prompt")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TargetResponse(BaseModel):
    """Standardized response from any target LLM adapter."""
    content: str
    raw_response: Optional[Dict[str, Any]] = None
    latency_ms: float
    model_name: str
    provider_name: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    error: Optional[str] = None


class EvaluationJudgement(BaseModel):
    """Judgement produced by the safety classifier / judge."""
    outcome: OutcomeClassification
    reasoning: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evaluator_name: str


class ProbeEvaluationResult(BaseModel):
    """Full outcome record for an executed safety probe."""
    probe_id: str
    name: str
    category: SafetyCategory
    strategy_name: str
    expected_outcome: OutcomeClassification
    outcome: OutcomeClassification
    is_safe: bool = Field(..., description="True if outcome aligns with safety expectations")
    reasoning: str
    turns_record: List[ProbeTurn]
    target_model: str
    target_provider: str
    total_latency_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StrategyMetrics(BaseModel):
    """Metrics aggregated per strategy."""
    strategy_name: str
    category: SafetyCategory
    total_probes: int
    refused_count: int
    non_compliant_count: int
    partial_count: int
    error_count: int
    safety_rate: float                # Percentage (0-100%)


class RunSummaryMetrics(BaseModel):
    """Aggregated metrics across an entire evaluation run."""
    total_probes: int
    total_refused: int
    total_non_compliant: int
    total_partial: int
    total_error: int
    safety_score: float               # Percentage of safe outcomes (0-100%)
    avg_latency_ms: float
    strategy_metrics: List[StrategyMetrics] = Field(default_factory=list)
    weakest_strategies: List[str] = Field(default_factory=list)


class RunReport(BaseModel):
    """Complete evaluation report artifact."""
    run_id: str
    target_model: str
    target_provider: str
    started_at: datetime
    completed_at: datetime
    metrics: RunSummaryMetrics
    results: List[ProbeEvaluationResult]
    config_snapshot: Dict[str, Any] = Field(default_factory=dict)


class ProbeRegressionItem(BaseModel):
    """Comparison of a single probe across baseline and candidate runs."""
    probe_id: str
    name: str
    strategy_name: str
    baseline_outcome: OutcomeClassification
    candidate_outcome: OutcomeClassification
    status_change: str               # "REGRESSED", "IMPROVED", "UNCHANGED", "NEW"


class RegressionDelta(BaseModel):
    """Comparative report between baseline and candidate run."""
    baseline_run_id: str
    candidate_run_id: str
    target_model_baseline: str
    target_model_candidate: str
    baseline_score: float
    candidate_score: float
    score_delta: float                # candidate_score - baseline_score
    overall_status: str              # "IMPROVED", "DEGRADED", "UNCHANGED"
    regressed_probes: List[ProbeRegressionItem] = Field(default_factory=list)
    improved_probes: List[ProbeRegressionItem] = Field(default_factory=list)
    unchanged_probes: List[ProbeRegressionItem] = Field(default_factory=list)
