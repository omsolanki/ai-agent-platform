# Cost Governance

## Why Cost Governance Matters

LLM API costs scale linearly with usage and exponentially with poor architecture decisions. Enterprise platforms must treat token consumption as a managed resource — like compute, storage, or network bandwidth.

## Cost Model

### Per-Agent Cost Breakdown

| Agent | Model | Avg Input Tokens | Avg Output Tokens | Cost/Request |
|-------|-------|-----------------|-------------------|-------------|
| Research | gpt-4o-mini | 800 | 600 | $0.0002 |
| Knowledge | gpt-4o-mini | 1,500 | 400 | $0.0003 |
| Summarization | gpt-4o-mini | 2,000 | 500 | $0.0004 |
| **Full Pipeline** | — | 4,300 | 1,500 | **$0.0009** |

### Model Pricing Reference

| Model | Input ($/1M tokens) | Output ($/1M tokens) | Use Case |
|-------|--------------------|--------------------|----------|
| gpt-4o | $2.50 | $10.00 | Complex reasoning |
| gpt-4o-mini | $0.15 | $0.60 | Standard agent tasks |
| gpt-3.5-turbo | $0.50 | $1.50 | Fallback / simple tasks |

## Cost Control Strategies

### 1. Model Selection Strategy

![Model Selection by Complexity](../diagrams/cost-model-tier.svg)

*Source: [cost-model-tier.d2](../diagrams/cost-model-tier.d2)*

**Implementation**: Router selects model tier based on query length, agent role, and tenant configuration.

### 2. Token Budgeting

```python
TOKEN_BUDGET_PER_REQUEST = 8000  # configurable per tenant

# Enforcement points:
# 1. Pre-execution: estimate and reject if over budget
# 2. Per-agent: truncate context if approaching limit
# 3. Post-execution: audit and alert on overruns
```

### 3. Prompt Optimization

| Technique | Token Savings | Implementation |
|-----------|--------------|----------------|
| System prompt caching | 30-50% | OpenAI prompt caching API |
| Context compression | 20-40% | Summarize prior context before passing |
| Structured output | 10-15% | JSON schema vs free-form text |
| Retrieval filtering | 15-25% | Top-k with relevance threshold |

### 4. Caching Strategy

![Query Caching Strategy](../diagrams/cost-cache.svg)

*Source: [cost-cache.d2](../diagrams/cost-cache.d2)*

**Cache layers**:
- L1: In-memory (per-process, 5min TTL)
- L2: Redis (shared, 1hr TTL)
- L3: LLM prompt cache (OpenAI native)

### 5. Rate Limiting

| Scope | Limit | Window |
|-------|-------|--------|
| Per user | 60 requests | 1 minute |
| Per tenant | 1,000 requests | 1 minute |
| Per agent | 200 executions | 1 minute |
| Global | 10,000 requests | 1 minute |

### 6. Fallback Models

![Model Fallback Chain](../diagrams/cost-fallback.svg)

*Source: [cost-fallback.d2](../diagrams/cost-fallback.d2)*

### 7. Agent Execution Limits

| Control | Value | Purpose |
|---------|-------|---------|
| Max agents per request | 3 | Prevent runaway pipelines |
| Max retries per agent | 3 | Limit retry cost |
| Max context window | 8,000 tokens | Prevent context bloat |
| Max retrieval chunks | 10 | Limit knowledge context |

## Sample Cost Calculations

### Scenario 1: Standard Enterprise Query

```
Query: "What are the compliance requirements for AI deployment?"
Route: Full Pipeline (3 agents)
Tokens: 4,300 input + 1,500 output = 5,800 total
Model: gpt-4o-mini
Cost: (4300 × $0.00000015) + (1500 × $0.0000006) = $0.0015
```

### Scenario 2: High-Volume Daily Operations

```
Assumptions:
  - 10,000 requests/day
  - 80% full pipeline, 20% knowledge-only
  - Average 5,800 tokens/request

Daily cost:
  - Full pipeline: 8,000 × $0.0015 = $12.00
  - Knowledge only: 2,000 × $0.0007 = $1.40
  - Total: $13.40/day = ~$402/month
```

### Scenario 3: With Caching (40% hit rate)

```
Effective requests: 6,000/day (4,000 cached)
Daily cost: $8.04/day = ~$241/month
Savings: 40% ($161/month)
```

### Scenario 4: Enterprise Scale (100K req/day)

```
Without optimization: $134/day = $4,020/month
With caching (40%): $80/day = $2,412/month
With model tiering: $60/day = $1,806/month
With prompt optimization: $45/day = $1,350/month
```

## Cost Dashboards

### Dashboard Metrics

| Panel | Query | Alert Threshold |
|-------|-------|----------------|
| Daily spend | `sum(request_cost_usd)` | > $50/day |
| Cost per agent | `sum by (agent)` | Agent > 60% of total |
| Token trend | `rate(agent_tokens_used_total[1h])` | > 2x baseline |
| Budget utilization | `tokens_used / token_budget` | > 80% |

## Governance Policies

1. **Pre-execution cost estimate** — API returns estimated cost before execution
2. **Tenant budgets** — Monthly caps with automatic throttling at 90%
3. **Cost attribution** — Tag every request with tenant, team, and use-case
4. **Anomaly detection** — Alert on 2x normal spend within 1 hour
5. **Monthly review** — Automated cost report with optimization recommendations
