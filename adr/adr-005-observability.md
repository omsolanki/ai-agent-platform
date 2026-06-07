# ADR-005: Observability Stack

## Status

Accepted

## Date

2025-06-07

## Context

Agentic AI systems are non-deterministic and require comprehensive observability for debugging, performance optimization, cost management, and quality assurance. The observability stack must be vendor-neutral and integrate with enterprise monitoring infrastructure.

## Decision Drivers

- Vendor neutrality (no lock-in)
- Industry standard protocols
- Three pillars: traces, metrics, logs
- Low operational overhead
- Agent-specific instrumentation

## Alternatives Considered

### 1. OpenTelemetry + Prometheus + Grafana (Selected)

**Pros**: Vendor-neutral, industry standard, rich ecosystem, self-hosted option, CNCF projects.

**Cons**: Operational overhead of self-hosted stack, configuration complexity.

### 2. Datadog

**Pros**: All-in-one, excellent LLM monitoring, low operational overhead.

**Cons**: Vendor lock-in, per-host pricing at scale, limited customization.

### 3. LangSmith

**Pros**: LLM-native, excellent for prompt debugging, LangChain integration.

**Cons**: LLM-focused only, not general infrastructure monitoring, vendor lock-in.

### 4. CloudWatch Only

**Pros**: Native AWS integration, managed, low ops.

**Cons**: Limited trace support, no Prometheus compatibility, AWS lock-in.

## Decision

**OpenTelemetry** for traces, **Prometheus** for metrics, **Grafana** for dashboards, **structlog** for structured logs.

## Instrumentation Points

| Component | Traces | Metrics | Logs |
|-----------|--------|---------|------|
| API endpoints | Request spans | Request count, latency | Access logs |
| Workflow engine | Workflow span | Execution count, latency | Workflow events |
| Each agent | Agent span | Execution count, tokens, latency | Agent events |
| LLM calls | LLM span | Latency, token count | Token usage |
| Memory service | Search span | Retrieval quality | Cache hits/misses |
| Governance | Guard span | Block count | Security events |

## Consequences

### Positive
- Portable across cloud providers
- Rich agent-specific instrumentation
- Standard Grafana dashboards reusable across projects
- No vendor lock-in for observability

### Negative
- Self-hosted stack requires operational expertise
- OTel collector configuration complexity
- Multiple systems to maintain (vs all-in-one)

## Future Evolution

- Add LangSmith for LLM-specific debugging (complementary, not replacement)
- Implement distributed trace correlation across agent services (Stage 2)
- Custom Grafana dashboards for cost and quality metrics
- Evaluate managed AMP/AMG on AWS for reduced ops
