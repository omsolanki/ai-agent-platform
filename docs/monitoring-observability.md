# Monitoring & Observability

## Observability Strategy

Enterprise agentic AI systems are inherently non-deterministic. Comprehensive observability is not optional — it is the primary mechanism for understanding, debugging, and improving agent behavior in production.

## Three Pillars

The observability stack is shown in the system context diagram (OTel traces, Prometheus metrics, Grafana dashboards). Dashed connectors denote metrics and trace flows.

![System Context — Observability](../diagrams/system-context.svg)

*Source: [system-context.d2](../diagrams/system-context.d2)*

## Metrics Catalog

### Workflow Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agent_workflow_executions_total` | Counter | strategy, status | Total workflow executions |
| `agent_workflow_latency_seconds` | Histogram | strategy | End-to-end workflow latency |
| `request_cost_usd` | Histogram | — | Cost per request |

### Agent Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agent_executions_total` | Counter | agent, status | Per-agent execution count |
| `agent_execution_latency_seconds` | Histogram | agent | Per-agent latency |
| `agent_tokens_used_total` | Counter | agent | Token consumption per agent |

### LLM Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `llm_request_latency_seconds` | Histogram | model | LLM API call latency |

### Quality Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `retrieval_quality_score` | Histogram | — | Knowledge retrieval quality |

## Trace Architecture

### Span Hierarchy

![Trace Span Hierarchy](../diagrams/observability-traces.svg)

*Source: [observability-traces.d2](../diagrams/observability-traces.d2)*

### Span Attributes

| Attribute | Example | Purpose |
|-----------|---------|---------|
| `request.id` | `uuid` | Correlate across systems |
| `agent.name` | `research_agent` | Identify agent |
| `agent.role` | `research` | Agent classification |
| `route.strategy` | `full_pipeline` | Routing decision |
| `query.length` | `156` | Input size tracking |

## Structured Logging

All logs are JSON-formatted via `structlog`:

```json
{
  "event": "workflow_completed",
  "timestamp": "2025-06-07T10:30:00Z",
  "level": "info",
  "request_id": "abc-123",
  "strategy": "full_pipeline",
  "tokens": 4500,
  "cost_usd": 0.0068,
  "latency_ms": 3200
}
```

### Log Levels by Event

| Event | Level | Fields |
|-------|-------|--------|
| Workflow started | INFO | request_id, strategy |
| Agent completed | INFO | agent, latency_ms, tokens |
| Agent failed | ERROR | agent, error |
| Governance blocked | WARNING | reason, severity |
| Circuit breaker open | ERROR | service, failures |

## Dashboard Design

### Dashboard 1: Platform Overview

- Workflow execution rate (req/min)
- Success vs failure rate
- P50/P95/P99 latency
- Total cost (hourly/daily)

### Dashboard 2: Agent Performance

- Per-agent execution count
- Per-agent latency distribution
- Per-agent token consumption
- Per-agent error rate

### Dashboard 3: Cost Analysis

- Cost per request distribution
- Cost by agent breakdown
- Token usage trends
- Budget utilization

### Dashboard 4: Quality Metrics

- Retrieval quality scores
- Evaluation scorecard trends
- Hallucination rate over time
- Groundedness scores

## Alerting Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| High error rate | > 5% failures in 5min | Critical |
| Latency spike | P95 > 30s for 10min | Warning |
| Cost anomaly | Hourly cost > 2x baseline | Warning |
| Circuit breaker | Any breaker open > 1min | Critical |
| Token budget | > 80% budget utilization | Warning |

## User Satisfaction Signals

Beyond technical metrics, track:

| Signal | Source | Implementation |
|--------|--------|----------------|
| Thumbs up/down | API feedback endpoint | Counter metric |
| Regeneration rate | Same query re-submitted | Anomaly detection |
| Session abandonment | No follow-up within 5min | Funnel metric |
| Human escalation | HITL agent triggered | Counter metric |

## Local Observability Stack

```bash
cd docker && docker-compose up -d
```

| Service | URL | Purpose |
|---------|-----|---------|
| Prometheus | http://localhost:9090 | Metrics collection |
| Grafana | http://localhost:3000 | Dashboards (admin/admin) |
| OTel Collector | localhost:4317 | Trace ingestion |
| API Metrics | http://localhost:8000/api/v1/metrics | App metrics endpoint |

## Production Recommendations

1. **Sampling**: Sample 10% of traces in production, 100% of errors
2. **Retention**: Metrics 90 days, traces 7 days, logs 30 days
3. **Cardinality**: Limit label cardinality (no user IDs in metric labels)
4. **Correlation**: Include `request_id` in all logs, traces, and audit entries
5. **SLOs**: Define latency SLO (P95 < 15s), availability SLO (99.9%)
