"""Agent Router — determines execution path based on request characteristics."""

from enum import Enum
from typing import Any

import structlog

from app.models.schemas import WorkflowRequest

logger = structlog.get_logger()


class RouteStrategy(str, Enum):
    FULL_PIPELINE = "full_pipeline"
    KNOWLEDGE_ONLY = "knowledge_only"
    RESEARCH_SUMMARY = "research_summary"
    DIRECT_SUMMARY = "direct_summary"


class AgentRouter:
    """
    Routes user requests to appropriate agent execution paths.

    Routing decisions consider query type, available context,
    cost budget, and explicit feature flags in the request.
    """

    def route(self, request: WorkflowRequest) -> RouteStrategy:
        flags = {
            "research": request.enable_research,
            "knowledge": request.enable_knowledge,
            "summarization": request.enable_summarization,
        }

        if all(flags.values()):
            strategy = RouteStrategy.FULL_PIPELINE
        elif flags["knowledge"] and flags["summarization"] and not flags["research"]:
            strategy = RouteStrategy.KNOWLEDGE_ONLY
        elif flags["research"] and flags["summarization"] and not flags["knowledge"]:
            strategy = RouteStrategy.RESEARCH_SUMMARY
        elif flags["summarization"] and not flags["research"] and not flags["knowledge"]:
            strategy = RouteStrategy.DIRECT_SUMMARY
        else:
            strategy = RouteStrategy.FULL_PIPELINE

        logger.info(
            "route_decision",
            strategy=strategy.value,
            query_length=len(request.query),
            flags=flags,
        )
        return strategy

    def get_agent_sequence(self, strategy: RouteStrategy) -> list[str]:
        """Return ordered agent names for the given routing strategy."""
        sequences = {
            RouteStrategy.FULL_PIPELINE: ["research_agent", "knowledge_agent", "summarization_agent"],
            RouteStrategy.KNOWLEDGE_ONLY: ["knowledge_agent", "summarization_agent"],
            RouteStrategy.RESEARCH_SUMMARY: ["research_agent", "summarization_agent"],
            RouteStrategy.DIRECT_SUMMARY: ["summarization_agent"],
        }
        return sequences[strategy]

    def should_retry(self, agent_name: str, error: str, retry_count: int, max_retries: int) -> bool:
        """Determine if agent execution should be retried."""
        transient_errors = ["timeout", "rate_limit", "503", "429", "connection"]
        is_transient = any(e in error.lower() for e in transient_errors)
        should = is_transient and retry_count < max_retries

        if should:
            logger.warning(
                "retry_scheduled",
                agent=agent_name,
                retry_count=retry_count + 1,
                error=error,
            )
        return should

    def estimate_cost(self, strategy: RouteStrategy, query_length: int) -> dict[str, Any]:
        """Estimate workflow cost based on routing strategy."""
        agent_costs = {
            "research_agent": 0.002,
            "knowledge_agent": 0.003,
            "summarization_agent": 0.001,
        }
        sequence = self.get_agent_sequence(strategy)
        base_cost = sum(agent_costs.get(a, 0.001) for a in sequence)
        length_multiplier = 1 + (query_length / 1000)
        estimated = base_cost * length_multiplier

        return {
            "strategy": strategy.value,
            "agents": sequence,
            "estimated_cost_usd": round(estimated, 4),
            "estimated_tokens": int(2000 * len(sequence) * length_multiplier),
        }
