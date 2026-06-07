"""Base agent abstraction with observability and cost tracking hooks."""

import time
from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_openai import ChatOpenAI

from app.config import Settings, get_settings
from app.models.schemas import AgentOutput, AgentRole
from app.monitoring.metrics import record_agent_execution
from app.monitoring.telemetry import get_tracer

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Abstract base for all platform agents."""

    role: AgentRole
    name: str

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.tracer = get_tracer()
        self._llm = ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key or "not-set",
            temperature=self.settings.openai_temperature,
            max_tokens=self.settings.openai_max_tokens,
        )

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> AgentOutput:
        """Execute agent logic with provided context."""

    async def run(self, context: dict[str, Any]) -> AgentOutput:
        """Run agent with tracing, metrics, and error handling."""
        start = time.perf_counter()
        span_name = f"agent.{self.name}.execute"

        with self.tracer.start_as_current_span(span_name) as span:
            span.set_attribute("agent.name", self.name)
            span.set_attribute("agent.role", self.role.value)

            try:
                output = await self.execute(context)
                latency_ms = (time.perf_counter() - start) * 1000
                output.latency_ms = latency_ms

                record_agent_execution(
                    agent_name=self.name,
                    success=output.success,
                    latency_ms=latency_ms,
                    tokens=output.tokens_used,
                )
                logger.info(
                    "agent_completed",
                    agent=self.name,
                    latency_ms=latency_ms,
                    tokens=output.tokens_used,
                )
                return output

            except Exception as exc:
                latency_ms = (time.perf_counter() - start) * 1000
                record_agent_execution(
                    agent_name=self.name,
                    success=False,
                    latency_ms=latency_ms,
                    tokens=0,
                )
                logger.error("agent_failed", agent=self.name, error=str(exc))
                span.record_exception(exc)
                return AgentOutput(
                    agent=self.role,
                    output={},
                    latency_ms=latency_ms,
                    success=False,
                    error=str(exc),
                )

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate for cost tracking (4 chars ≈ 1 token)."""
        return max(1, len(text) // 4)

    def _estimate_cost(self, tokens: int, model: str | None = None) -> float:
        """Estimate cost in USD based on model pricing."""
        model = model or self.settings.openai_model
        rates = {
            "gpt-4o": 0.005 / 1000,
            "gpt-4o-mini": 0.00015 / 1000,
            "gpt-3.5-turbo": 0.0005 / 1000,
        }
        rate = rates.get(model, 0.00015 / 1000)
        return tokens * rate
