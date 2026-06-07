# ADR-003: Agent Routing Strategy

## Status

Accepted

## Date

2025-06-07

## Context

Not every user request requires the full three-agent pipeline. Routing must balance response quality, latency, and cost by selecting the optimal agent execution path per request.

## Decision Drivers

- Cost optimization (skip unnecessary agents)
- Latency reduction (fewer agents = faster response)
- Quality maintenance (don't skip agents when needed)
- Explicit user control (feature flags)
- Extensibility for future agents

## Alternatives Considered

### 1. Static Pipeline (All Agents Always)

**Pros**: Maximum quality, simple implementation.

**Cons**: 3x cost for simple queries, unnecessary latency.

### 2. LLM-Based Router

**Pros**: Intelligent routing based on query semantics.

**Cons**: Additional LLM call cost, latency, non-deterministic routing.

### 3. Rule-Based Router with Feature Flags (Selected)

**Pros**: Deterministic, zero cost, explicit control, easy to test.

**Cons**: Less intelligent than LLM router, requires manual rule maintenance.

### 4. User-Selected Pipeline

**Pros**: Full user control.

**Cons**: Poor UX, requires AI literacy, error-prone.

## Decision

**Rule-based router** with request feature flags and predefined route strategies.

## Route Strategies

| Strategy | Agents | Use Case |
|----------|--------|----------|
| `full_pipeline` | Research → Knowledge → Summarization | Complex research queries |
| `knowledge_only` | Knowledge → Summarization | Factual lookup with KB |
| `research_summary` | Research → Summarization | External research, no KB |
| `direct_summary` | Summarization | Summarize provided context |

## Consequences

### Positive
- Zero routing overhead (no additional LLM call)
- Deterministic and testable
- Cost estimation possible before execution
- Users can explicitly control agent selection

### Negative
- Cannot adapt to query semantics automatically
- New routes require code changes
- May over-provision agents for simple queries when defaults are used

## Future Evolution

- Add LLM-based router as optional enhancement (Stage 2)
- Query complexity scoring for automatic route selection
- Per-tenant routing policies
- A/B testing of routing strategies
