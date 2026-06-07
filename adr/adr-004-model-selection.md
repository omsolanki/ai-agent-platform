# ADR-004: Model Selection Strategy

## Status

Accepted

## Date

2025-06-07

## Context

LLM model selection directly impacts cost, latency, and output quality. The platform must define a model selection strategy that balances these factors across different agent roles and query types.

## Decision Drivers

- Cost per request target: < $0.01
- Latency target: < 15s end-to-end
- Quality target: > 0.85 evaluation score
- Provider flexibility (avoid lock-in)
- Fallback capability

## Alternatives Considered

### 1. Single Model (gpt-4o-mini) for All Agents

**Pros**: Simple, consistent quality, one integration.

**Cons**: Over-provisioned for summarization, no cost optimization.

### 2. Tiered Models per Agent Role (Selected)

**Pros**: Cost-optimized per task, quality where needed, clear upgrade path.

**Cons**: Multiple model configurations, potential quality variance.

### 3. gpt-4o for Everything

**Pros**: Maximum quality.

**Cons**: 10-15x cost increase, unnecessary for structured tasks.

### 4. Open-Source Models (Llama, Mistral)

**Pros**: No per-token cost, data sovereignty.

**Cons**: Self-hosting infrastructure, quality gap, operational overhead.

## Decision

**Tiered model selection** with gpt-4o-mini as default, gpt-4o for complex tasks, gpt-3.5-turbo as fallback.

## Model Assignment

| Agent | Default Model | Upgrade Trigger | Fallback |
|-------|--------------|-----------------|----------|
| Research | gpt-4o-mini | Multi-source synthesis | gpt-3.5-turbo |
| Knowledge | gpt-4o-mini | Low retrieval confidence | gpt-3.5-turbo |
| Summarization | gpt-4o-mini | Executive/compliance docs | gpt-3.5-turbo |

## Cost Impact

| Configuration | Cost/Request | Monthly (10K req/day) |
|--------------|-------------|----------------------|
| All gpt-4o | $0.015 | $4,500 |
| Tiered (selected) | $0.001 | $300 |
| All gpt-3.5-turbo | $0.0005 | $150 |

## Consequences

### Positive
- 90%+ cost reduction vs all-gpt-4o
- Quality maintained for structured agent tasks
- Clear fallback path for reliability

### Negative
- Quality variance between model tiers
- OpenAI dependency (mitigated by abstraction layer)
- Model pricing changes require strategy review

## Future Evolution

- Add model performance benchmarking pipeline
- Evaluate open-source models for summarization (cost savings)
- Implement automatic model upgrade based on evaluation scores
- Multi-provider support (Anthropic, Google) via LangChain abstraction
