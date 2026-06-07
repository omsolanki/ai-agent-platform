"""API route definitions."""

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from prometheus_client import generate_latest

from app.api.history import save_run_snapshot, snapshot_to_detail, snapshot_to_entry
from app.evaluation.service import EvaluationService
from app.governance.guards import GovernanceGuard
from app.models.schemas import (
    EvaluationScorecard,
    GovernanceResult,
    WorkflowHistoryDetail,
    WorkflowHistoryEntry,
    WorkflowRequest,
    WorkflowResponse,
    WorkflowRunResponse,
    WorkflowStatus,
)
from app.orchestration.router import AgentRouter
from app.orchestration.workflow import WorkflowEngine

router = APIRouter()
workflow_engine = WorkflowEngine()
evaluation_service = EvaluationService()
agent_router = AgentRouter()
governance_guard = GovernanceGuard(workflow_engine.settings)


def _check_governance(query: str) -> GovernanceResult:
    return governance_guard.audit_request(query)


def _governance_http_error(governance: GovernanceResult) -> HTTPException:
    failed = next((c for c in governance.checks if not c.passed), None)
    message = failed.reason if failed else "Governance check failed"
    return HTTPException(
        status_code=422,
        detail={"message": message, "governance": governance.model_dump()},
    )


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-agent-platform",
        "version": "1.0.0",
    }


@router.post("/workflow/execute", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest):
    """Execute the multi-agent workflow pipeline."""
    governance = _check_governance(request.query)
    if not governance.passed:
        raise _governance_http_error(governance)

    try:
        result = await workflow_engine.execute(request)
        return WorkflowResponse(
            request_id=result.request_id,
            trace_id=result.trace_id,
            status=result.status,
            result=result,
            governance=governance,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/workflow/run", response_model=WorkflowRunResponse)
async def run_workflow(request: WorkflowRequest):
    """Execute workflow, evaluate quality, and return governance + routing in one response."""
    governance = _check_governance(request.query)
    if not governance.passed:
        raise _governance_http_error(governance)

    strategy = agent_router.route(request)
    routing = agent_router.estimate_cost(strategy, len(request.query))

    result = await workflow_engine.execute(request)
    if result.status != WorkflowStatus.COMPLETED:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Workflow did not complete successfully",
                "request_id": result.request_id,
                "governance": governance.model_dump(),
            },
        )

    scorecard = await evaluation_service.evaluate(result)
    await save_run_snapshot(workflow_engine, request.query, result, scorecard, governance)

    return WorkflowRunResponse(
        result=result,
        scorecard=scorecard,
        governance=governance,
        routing=routing,
    )


@router.post("/workflow/evaluate", response_model=EvaluationScorecard)
async def evaluate_workflow(request: WorkflowRequest):
    """Execute workflow and return evaluation scorecard."""
    governance = _check_governance(request.query)
    if not governance.passed:
        raise _governance_http_error(governance)

    result = await workflow_engine.execute(request)
    if result.status != WorkflowStatus.COMPLETED:
        raise HTTPException(status_code=422, detail="Workflow did not complete successfully")
    return await evaluation_service.evaluate(result)


@router.post("/workflow/execute/stream")
async def execute_workflow_stream(request: WorkflowRequest):
    """Stream workflow progress via Server-Sent Events."""
    governance = _check_governance(request.query)
    if not governance.passed:
        raise _governance_http_error(governance)

    queue: asyncio.Queue[tuple[str, dict[str, Any]] | None] = asyncio.Queue()

    async def on_progress(event: str, data: dict[str, Any]) -> None:
        await queue.put((event, data))

    async def run_workflow() -> None:
        try:
            result = await workflow_engine.execute(request, on_progress=on_progress)
            if result.status == WorkflowStatus.COMPLETED:
                scorecard = await evaluation_service.evaluate(result)
                await save_run_snapshot(workflow_engine, request.query, result, scorecard, governance)
                await queue.put(("scorecard", scorecard.model_dump(mode="json")))
        except Exception as exc:
            await queue.put(("error", {"message": str(exc)}))
        finally:
            await queue.put(None)

    async def event_generator():
        task = asyncio.create_task(run_workflow())
        while True:
            item = await queue.get()
            if item is None:
                break
            event_type, data = item
            yield _format_sse(event_type, data)
        await task

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/workflow/history", response_model=list[WorkflowHistoryEntry])
async def list_workflow_history(limit: int = 10):
    """Return recent workflow run summaries."""
    limit = min(max(limit, 1), 50)
    snapshots = await workflow_engine.memory.list_run_history(limit=limit)
    return [snapshot_to_entry(snapshot) for snapshot in snapshots]


@router.get("/workflow/history/{request_id}", response_model=WorkflowHistoryDetail)
async def get_workflow_history(request_id: str):
    """Return a full snapshot for a previous workflow run."""
    snapshot = await workflow_engine.memory.get_run_snapshot(request_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return snapshot_to_detail(snapshot)


@router.post("/workflow/estimate-cost")
async def estimate_cost(request: WorkflowRequest):
    """Estimate workflow cost without execution."""
    strategy = agent_router.route(request)
    return agent_router.estimate_cost(strategy, len(request.query))


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    from starlette.responses import Response

    return Response(content=generate_latest(), media_type="text/plain")


def _format_sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"
