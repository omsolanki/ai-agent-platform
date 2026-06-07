"""Pydantic schemas for agent inputs, outputs, and API contracts."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    RESEARCH = "research"
    KNOWLEDGE = "knowledge"
    SUMMARIZATION = "summarization"


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ConfidenceIndicator(BaseModel):
    score: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    rationale: str = ""
    source_count: int = 0


class ResearchFinding(BaseModel):
    topic: str
    findings: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    confidence: ConfidenceIndicator
    metadata: dict[str, Any] = Field(default_factory=dict)


class GroundedResponse(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    confidence: ConfidenceIndicator
    retrieved_chunks: int = 0


class ActionItem(BaseModel):
    description: str
    priority: str = "medium"
    owner: str | None = None


class ExecutiveSummary(BaseModel):
    headline: str
    key_insights: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    detailed_summary: str = ""


class AgentOutput(BaseModel):
    agent: AgentRole
    output: dict[str, Any]
    tokens_used: int = 0
    latency_ms: float = 0.0
    model: str = ""
    success: bool = True
    error: str | None = None


class FinalResponse(BaseModel):
    request_id: str
    executive_summary: ExecutiveSummary
    grounded_response: GroundedResponse | None = None
    research_findings: ResearchFinding | None = None
    agent_outputs: list[AgentOutput] = Field(default_factory=list)
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    status: WorkflowStatus = WorkflowStatus.COMPLETED


class WorkflowRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    enable_research: bool = True
    enable_knowledge: bool = True
    enable_summarization: bool = True


class WorkflowResponse(BaseModel):
    request_id: str
    status: WorkflowStatus
    result: FinalResponse | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EvaluationScorecard(BaseModel):
    request_id: str
    task_completion: float = Field(ge=0.0, le=1.0)
    answer_quality: float = Field(ge=0.0, le=1.0)
    groundedness: float = Field(ge=0.0, le=1.0)
    hallucination_rate: float = Field(ge=0.0, le=1.0)
    agent_accuracy: float = Field(ge=0.0, le=1.0)
    workflow_success: bool = True
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    cost_efficiency: float = Field(ge=0.0, le=1.0)
    notes: str = ""
