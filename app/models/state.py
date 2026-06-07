"""Workflow and agent state models for LangGraph orchestration."""

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages

from app.models.schemas import (
    AgentOutput,
    ExecutiveSummary,
    GroundedResponse,
    ResearchFinding,
    WorkflowStatus,
)


class AgentState(TypedDict, total=False):
    """Per-agent execution state."""

    agent_name: str
    input_context: dict[str, Any]
    output: dict[str, Any]
    tokens_used: int
    latency_ms: float
    retry_count: int
    error: str | None


class WorkflowState(TypedDict, total=False):
    """Shared workflow state passed between agents via LangGraph."""

    request_id: str
    query: str
    session_id: str | None
    status: WorkflowStatus
    messages: Annotated[list, add_messages]
    research_findings: ResearchFinding | None
    grounded_response: GroundedResponse | None
    executive_summary: ExecutiveSummary | None
    agent_outputs: list[AgentOutput]
    shared_memory: dict[str, Any]
    total_tokens: int
    total_cost_usd: float
    errors: list[str]
    retry_count: int
    current_agent: str | None
