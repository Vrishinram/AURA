"""
AI Safety Red Team Agent Evaluation Loop.
"""

import time
from typing import Callable, List, Optional
from aura_safety.adapters.base import BaseTargetAdapter
from aura_safety.engine.classifier import SafetyClassifier
from aura_safety.schemas import (
    ChatMessage,
    OutcomeClassification,
    ProbeEvaluationResult,
    ProbeTurn,
    SafetyProbe,
)


class SafetyRedTeamAgent:
    """
    Automated agent that probes target models with safety strategies,
    records multi-turn trajectories, and classifies outcomes.
    """

    def __init__(
        self,
        target_adapter: BaseTargetAdapter,
        classifier: Optional[SafetyClassifier] = None,
    ):
        self.target_adapter = target_adapter
        self.classifier = classifier or SafetyClassifier()

    def run_single_probe(self, probe: SafetyProbe) -> ProbeEvaluationResult:
        """Executes a single probe (single-turn or multi-turn) against the target model."""
        turns_record: List[ProbeTurn] = []
        chat_history: List[ChatMessage] = []
        total_latency = 0.0

        # Include custom system prompt in chat history if present
        if probe.system_prompt:
            chat_history.append(ChatMessage(role="system", content=probe.system_prompt))

        for idx, user_prompt in enumerate(probe.turns):
            chat_history.append(ChatMessage(role="user", content=user_prompt))

            # Dispatch to target adapter
            if len(chat_history) == 1 and not probe.system_prompt:
                # Single prompt fast path
                target_resp = self.target_adapter.send_prompt(user_prompt)
            else:
                target_resp = self.target_adapter.send_chat(chat_history)

            total_latency += target_resp.latency_ms

            # Append assistant response to history for subsequent turns
            if target_resp.content:
                chat_history.append(ChatMessage(role="assistant", content=target_resp.content))

            turn = ProbeTurn(
                turn_index=idx,
                user_prompt=user_prompt,
                system_prompt=probe.system_prompt,
                model_response=target_resp.content,
                latency_ms=target_resp.latency_ms,
                error=target_resp.error,
            )
            turns_record.append(turn)

            # If an error occurred, break early
            if target_resp.error:
                break

        # Classify the outcome
        judgement = self.classifier.evaluate_probe_run(probe, turns_record)

        is_safe = (judgement.outcome == probe.expected_outcome)

        return ProbeEvaluationResult(
            probe_id=probe.probe_id,
            name=probe.name,
            category=probe.category,
            strategy_name=probe.strategy_name,
            expected_outcome=probe.expected_outcome,
            outcome=judgement.outcome,
            is_safe=is_safe,
            reasoning=judgement.reasoning,
            turns_record=turns_record,
            target_model=self.target_adapter.model_name,
            target_provider=self.target_adapter.provider_name,
            total_latency_ms=total_latency,
            metadata=probe.metadata,
        )

    def run_suite(
        self,
        probes: List[SafetyProbe],
        progress_callback: Optional[Callable[[int, int, ProbeEvaluationResult], None]] = None,
    ) -> List[ProbeEvaluationResult]:
        """
        Executes a full suite of safety probes sequentially and records outcomes.
        """
        results: List[ProbeEvaluationResult] = []
        total = len(probes)

        for idx, probe in enumerate(probes):
            result = self.run_single_probe(probe)
            results.append(result)
            if progress_callback:
                progress_callback(idx + 1, total, result)

        return results
