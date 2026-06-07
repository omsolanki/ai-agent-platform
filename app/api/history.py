"""Helpers for persisting and loading workflow run history."""

from datetime import UTC, datetime
from typing import Any

from app.models.schemas import (
    EvaluationScorecard,
    FinalResponse,
    GovernanceResult,
    ScorecardSummary,
    WorkflowHistoryDetail,
    WorkflowHistoryEntry,
    WorkflowStatus,
)
from app.orchestration.workflow import WorkflowEngine


async def save_run_snapshot(
    engine: WorkflowEngine,
    query: str,
    result: FinalResponse,
    scorecard: EvaluationScorecard | None = None,
    governance: GovernanceResult | None = None,
) -> None:
    if result.status != WorkflowStatus.COMPLETED:
        return

    summary = None
    if scorecard:
        summary = ScorecardSummary(
            task_completion=scorecard.task_completion,
            groundedness=scorecard.groundedness,
            hallucination_rate=scorecard.hallucination_rate,
            workflow_success=scorecard.workflow_success,
        )

    snapshot: dict[str, Any] = {
        "request_id": result.request_id,
        "trace_id": result.trace_id,
        "query": query,
        "status": result.status.value,
        "cost_usd": result.total_cost_usd,
        "latency_ms": result.total_latency_ms,
        "timestamp": datetime.now(UTC).isoformat(),
        "scorecard_summary": summary.model_dump(mode="json") if summary else None,
        "result": result.model_dump(mode="json"),
        "scorecard": scorecard.model_dump(mode="json") if scorecard else None,
        "governance": governance.model_dump(mode="json") if governance else None,
    }
    await engine.memory.save_run_snapshot(snapshot)


def snapshot_to_entry(snapshot: dict[str, Any]) -> WorkflowHistoryEntry:
    summary_data = snapshot.get("scorecard_summary")
    return WorkflowHistoryEntry(
        request_id=snapshot["request_id"],
        trace_id=snapshot.get("trace_id"),
        query=snapshot["query"],
        status=WorkflowStatus(snapshot["status"]),
        cost_usd=snapshot.get("cost_usd", 0.0),
        latency_ms=snapshot.get("latency_ms", 0.0),
        timestamp=datetime.fromisoformat(snapshot["timestamp"]),
        scorecard_summary=ScorecardSummary(**summary_data) if summary_data else None,
    )


def snapshot_to_detail(snapshot: dict[str, Any]) -> WorkflowHistoryDetail:
    entry = snapshot_to_entry(snapshot)
    scorecard_data = snapshot.get("scorecard")
    governance_data = snapshot.get("governance")
    return WorkflowHistoryDetail(
        **entry.model_dump(),
        result=FinalResponse(**snapshot["result"]),
        scorecard=EvaluationScorecard(**scorecard_data) if scorecard_data else None,
        governance=GovernanceResult(**governance_data) if governance_data else None,
    )
