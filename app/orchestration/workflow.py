"""LangGraph workflow execution engine for multi-agent orchestration."""

import time
from typing import Any
from uuid import uuid4

import structlog
from langgraph.graph import END, StateGraph

from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.research_agent import ResearchAgent
from app.agents.summarization_agent import SummarizationAgent
from app.config import Settings, get_settings
from app.governance.guards import GovernanceGuard
from app.memory.service import MemoryService
from app.models.schemas import (
    AgentOutput,
    ExecutiveSummary,
    FinalResponse,
    GroundedResponse,
    ResearchFinding,
    WorkflowRequest,
    WorkflowStatus,
)
from app.models.state import WorkflowState
from app.monitoring.metrics import record_workflow_execution
from app.monitoring.telemetry import get_tracer
from app.orchestration.router import AgentRouter, RouteStrategy

logger = structlog.get_logger()


class WorkflowEngine:
    """
    Orchestrates multi-agent workflows using LangGraph state management.

    Flow: User Request → Router → Research → Knowledge → Summarization → Response
    """

    def __init__(
        self,
        settings: Settings | None = None,
        memory_service: MemoryService | None = None,
    ):
        self.settings = settings or get_settings()
        self.memory = memory_service or MemoryService(self.settings)
        self.router = AgentRouter()
        self.guard = GovernanceGuard(self.settings)
        self.tracer = get_tracer()

        self.research_agent = ResearchAgent(self.settings)
        self.knowledge_agent = KnowledgeAgent(self.memory, settings=self.settings)
        self.summarization_agent = SummarizationAgent(self.settings)

        self._agents = {
            "research_agent": self.research_agent,
            "knowledge_agent": self.knowledge_agent,
            "summarization_agent": self.summarization_agent,
        }

    def _build_graph(self, agent_sequence: list[str]) -> StateGraph:
        """Build LangGraph workflow for the given agent sequence."""
        graph = StateGraph(WorkflowState)

        for agent_name in agent_sequence:
            graph.add_node(agent_name, self._make_agent_node(agent_name))

        for i in range(len(agent_sequence) - 1):
            graph.add_edge(agent_sequence[i], agent_sequence[i + 1])

        graph.set_entry_point(agent_sequence[0])
        graph.add_edge(agent_sequence[-1], END)

        return graph

    def _make_agent_node(self, agent_name: str):
        """Create a LangGraph node function for the given agent."""

        async def node(state: WorkflowState) -> dict[str, Any]:
            agent = self._agents[agent_name]
            context = {
                "query": state.get("query", ""),
                "shared_memory": state.get("shared_memory", {}),
                "research_findings": (
                    state["research_findings"].model_dump()
                    if state.get("research_findings")
                    else {}
                ),
                "grounded_response": (
                    state["grounded_response"].model_dump()
                    if state.get("grounded_response")
                    else {}
                ),
            }

            output = await agent.run(context)
            updates: dict[str, Any] = {
                "current_agent": agent_name,
                "agent_outputs": state.get("agent_outputs", []) + [output],
                "total_tokens": state.get("total_tokens", 0) + output.tokens_used,
            }

            if output.success:
                if agent_name == "research_agent":
                    updates["research_findings"] = ResearchFinding(**output.output)
                elif agent_name == "knowledge_agent":
                    updates["grounded_response"] = GroundedResponse(**output.output)
                elif agent_name == "summarization_agent":
                    updates["executive_summary"] = ExecutiveSummary(**output.output)
            else:
                errors = state.get("errors", [])
                errors.append(f"{agent_name}: {output.error}")
                updates["errors"] = errors

                if self.router.should_retry(
                    agent_name,
                    output.error or "unknown",
                    state.get("retry_count", 0),
                    self.settings.max_agent_retries,
                ):
                    updates["retry_count"] = state.get("retry_count", 0) + 1
                    updates["status"] = WorkflowStatus.RETRYING

            return updates

        return node

    async def execute(self, request: WorkflowRequest) -> FinalResponse:
        """Execute the full agent workflow for a user request."""
        request_id = str(uuid4())
        start = time.perf_counter()

        with self.tracer.start_as_current_span("workflow.execute") as span:
            span.set_attribute("request.id", request_id)
            span.set_attribute("query.length", len(request.query))

            guard_result = self.guard.validate_request(request.query)
            if not guard_result.passed:
                logger.warning("governance_blocked", reason=guard_result.reason)
                return FinalResponse(
                    request_id=request_id,
                    executive_summary=ExecutiveSummary(
                        headline="Request blocked by governance policy",
                        key_insights=[guard_result.reason],
                    ),
                    status=WorkflowStatus.FAILED,
                )

            session_id = await self.memory.get_or_create_session(request.session_id)
            strategy = self.router.route(request)
            agent_sequence = self.router.get_agent_sequence(strategy)

            span.set_attribute("route.strategy", strategy.value)
            span.set_attribute("route.agents", ",".join(agent_sequence))

            initial_state: WorkflowState = {
                "request_id": request_id,
                "query": request.query,
                "session_id": session_id,
                "status": WorkflowStatus.RUNNING,
                "messages": [],
                "shared_memory": self.memory.build_shared_memory(session_id, request.context),
                "agent_outputs": [],
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "errors": [],
                "retry_count": 0,
            }

            graph = self._build_graph(agent_sequence)
            compiled = graph.compile()

            try:
                final_state = await compiled.ainvoke(initial_state)
            except Exception as exc:
                logger.error("workflow_failed", request_id=request_id, error=str(exc))
                latency_ms = (time.perf_counter() - start) * 1000
                record_workflow_execution(success=False, latency_ms=latency_ms, strategy=strategy.value)
                return FinalResponse(
                    request_id=request_id,
                    executive_summary=ExecutiveSummary(
                        headline="Workflow execution failed",
                        key_insights=[str(exc)],
                    ),
                    status=WorkflowStatus.FAILED,
                    total_latency_ms=latency_ms,
                )

            total_tokens = final_state.get("total_tokens", 0)
            total_cost = self._estimate_total_cost(final_state.get("agent_outputs", []))
            latency_ms = (time.perf_counter() - start) * 1000
            has_errors = bool(final_state.get("errors"))

            response = FinalResponse(
                request_id=request_id,
                executive_summary=final_state.get("executive_summary")
                or ExecutiveSummary(headline="No summary generated"),
                grounded_response=final_state.get("grounded_response"),
                research_findings=final_state.get("research_findings"),
                agent_outputs=final_state.get("agent_outputs", []),
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
                total_latency_ms=latency_ms,
                status=WorkflowStatus.FAILED if has_errors else WorkflowStatus.COMPLETED,
            )

            await self.memory.persist_workflow(request_id, final_state)
            record_workflow_execution(
                success=not has_errors,
                latency_ms=latency_ms,
                strategy=strategy.value,
            )

            logger.info(
                "workflow_completed",
                request_id=request_id,
                strategy=strategy.value,
                tokens=total_tokens,
                cost_usd=total_cost,
                latency_ms=latency_ms,
            )
            return response

    def _estimate_total_cost(self, outputs: list[AgentOutput]) -> float:
        total = 0.0
        for output in outputs:
            agent = self._agents.get(f"{output.agent.value}_agent")
            if agent:
                total += agent._estimate_cost(output.tokens_used, output.model)
        return round(total, 6)
