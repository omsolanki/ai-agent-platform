"""Prometheus metrics for agent and workflow observability."""

from prometheus_client import Counter, Histogram, Info

# Workflow metrics
WORKFLOW_EXECUTIONS = Counter(
    "agent_workflow_executions_total",
    "Total workflow executions",
    ["strategy", "status"],
)

WORKFLOW_LATENCY = Histogram(
    "agent_workflow_latency_seconds",
    "Workflow end-to-end latency",
    ["strategy"],
    buckets=[0.5, 1, 2, 5, 10, 30, 60],
)

# Agent metrics
AGENT_EXECUTIONS = Counter(
    "agent_executions_total",
    "Total agent executions",
    ["agent", "status"],
)

AGENT_LATENCY = Histogram(
    "agent_execution_latency_seconds",
    "Per-agent execution latency",
    ["agent"],
    buckets=[0.1, 0.5, 1, 2, 5, 10],
)

AGENT_TOKENS = Counter(
    "agent_tokens_used_total",
    "Total tokens consumed per agent",
    ["agent"],
)

# LLM metrics
LLM_LATENCY = Histogram(
    "llm_request_latency_seconds",
    "LLM API call latency",
    ["model"],
    buckets=[0.5, 1, 2, 5, 10, 30],
)

# Cost metrics
REQUEST_COST = Histogram(
    "request_cost_usd",
    "Estimated cost per request in USD",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5],
)

# Retrieval metrics
RETRIEVAL_QUALITY = Histogram(
    "retrieval_quality_score",
    "Knowledge retrieval quality score",
    buckets=[0.1, 0.3, 0.5, 0.7, 0.9, 1.0],
)

PLATFORM_INFO = Info("agent_platform", "Platform version and configuration")


def setup_metrics(version: str = "1.0.0") -> None:
    """Initialize platform info metrics."""
    PLATFORM_INFO.info({"version": version, "framework": "langgraph"})


def record_workflow_execution(success: bool, latency_ms: float, strategy: str) -> None:
    status = "success" if success else "failure"
    WORKFLOW_EXECUTIONS.labels(strategy=strategy, status=status).inc()
    WORKFLOW_LATENCY.labels(strategy=strategy).observe(latency_ms / 1000)


def record_agent_execution(
    agent_name: str, success: bool, latency_ms: float, tokens: int
) -> None:
    status = "success" if success else "failure"
    AGENT_EXECUTIONS.labels(agent=agent_name, status=status).inc()
    AGENT_LATENCY.labels(agent=agent_name).observe(latency_ms / 1000)
    if tokens > 0:
        AGENT_TOKENS.labels(agent=agent_name).inc(tokens)
