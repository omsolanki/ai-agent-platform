"""API route definitions."""

from fastapi import APIRouter, HTTPException
from prometheus_client import generate_latest

from app.evaluation.service import EvaluationService
from app.models.schemas import EvaluationScorecard, WorkflowRequest, WorkflowResponse, WorkflowStatus
from app.orchestration.router import AgentRouter
from app.orchestration.workflow import WorkflowEngine

router = APIRouter()
workflow_engine = WorkflowEngine()
evaluation_service = EvaluationService()
agent_router = AgentRouter()


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
    try:
        result = await workflow_engine.execute(request)
        return WorkflowResponse(
            request_id=result.request_id,
            status=result.status,
            result=result,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/workflow/evaluate", response_model=EvaluationScorecard)
async def evaluate_workflow(request: WorkflowRequest):
    """Execute workflow and return evaluation scorecard."""
    result = await workflow_engine.execute(request)
    if result.status != WorkflowStatus.COMPLETED:
        raise HTTPException(status_code=422, detail="Workflow did not complete successfully")
    return await evaluation_service.evaluate(result)


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
