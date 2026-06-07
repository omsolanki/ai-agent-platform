# System Architecture

## Executive Overview

The AI Agent Platform is an enterprise reference implementation demonstrating how production-grade agentic AI systems are designed, orchestrated, monitored, governed, and deployed. It is **not a chatbot** — it is an architecture showcase for multi-agent workflow automation.

## Architecture Principles

| Principle | Description |
|-----------|-------------|
| **Separation of Concerns** | Agents, orchestration, memory, governance, and observability are independently evolvable layers |
| **Stateless Agents, Stateful Workflows** | Agents are stateless executors; LangGraph manages workflow state and context passing |
| **Governance by Default** | Every request passes through policy guards before agent execution |
| **Observable Everything** | Traces, metrics, and structured logs cover every agent transition |
| **Cost-Aware Execution** | Token budgets, model tiers, and cost estimation are first-class concerns |

## System Context

![System Context](../diagrams/system-context.svg)

*Source: [system-context.d2](../diagrams/system-context.d2)*

## Layer Architecture

### 1. API Layer (FastAPI)

- RESTful endpoints for workflow execution, evaluation, and cost estimation
- Request validation via Pydantic schemas
- Prometheus metrics endpoint
- OpenAPI documentation auto-generated

### 2. Orchestration Layer (LangGraph)

- Stateful workflow graph with checkpointing support
- Agent Router determines execution path
- Shared memory context passed between agents
- Retry handling and failure recovery built into graph nodes

### 3. Agent Layer

Three specialized agents with single responsibilities:

| Agent | Input | Output | Model Tier |
|-------|-------|--------|------------|
| Research | User query + conversation context | Structured findings, references, confidence | Standard |
| Knowledge | Query + research context + vector retrieval | Grounded answer, citations, confidence | Standard |
| Summarization | Research + knowledge outputs | Executive summary, action items | Economy |

### 4. Memory Layer

![Memory Architecture](../diagrams/memory-architecture.svg)

*Source: [memory-architecture.d2](../diagrams/memory-architecture.d2)*

Dual-store architecture:

- **Short-term**: In-process shared memory via LangGraph state (conversation context, agent outputs)
- **Long-term Vector**: Qdrant for semantic knowledge retrieval
- **Long-term Metadata**: PostgreSQL for sessions, workflows, audit logs

### 5. Governance Layer

- Prompt injection detection
- PII filtering
- Token budget enforcement
- Blocked topic policies
- Audit logging for all workflow events

### 6. Observability Layer

- **Traces**: OpenTelemetry spans per agent and workflow
- **Metrics**: Prometheus counters/histograms for latency, tokens, cost
- **Logs**: Structured JSON logging via structlog
- **Dashboards**: Grafana with Prometheus datasource

## Interaction Flow

![Agent Interaction Flow](../diagrams/agent-interaction.svg)

*Source: [agent-interaction.d2](../diagrams/agent-interaction.d2)*

## State Management

LangGraph `WorkflowState` carries:

- `request_id`, `query`, `session_id` — identity
- `research_findings`, `grounded_response`, `executive_summary` — agent outputs
- `agent_outputs[]` — execution metadata per agent
- `shared_memory` — conversation history and user context
- `total_tokens`, `total_cost_usd` — cost tracking
- `errors[]`, `retry_count` — failure state

State is immutable per node — each agent node returns partial state updates that LangGraph merges.

## Failure Handling

| Failure Type | Strategy |
|-------------|----------|
| Transient (timeout, 429, 503) | Exponential backoff retry (max 3) |
| Agent execution error | Log, record in state.errors, continue or fail based on severity |
| Governance violation | Immediate rejection, no agent execution |
| Token budget exceeded | Halt workflow, return partial results |
| External service down | Circuit breaker pattern, fallback to mock/degraded mode |

## Scaling Strategy

See [tradeoffs.md](tradeoffs.md) for the four-stage evolution model:

1. **Stage 1**: Single-process runtime (current implementation)
2. **Stage 2**: Distributed agent services behind message queue
3. **Stage 3**: Dedicated memory layer with read replicas
4. **Stage 4**: Enterprise multi-tenant platform with agent marketplace

## Technology Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Orchestration | LangGraph | Native state management, graph-based workflows, checkpointing |
| API Framework | FastAPI | Async-native, auto OpenAPI, Pydantic integration |
| Vector Store | Qdrant | High-performance, self-hosted, filtering support |
| Metadata Store | PostgreSQL | ACID compliance, JSONB for flexible state, mature ecosystem |
| LLM Provider | OpenAI | Industry standard, function calling, model tier flexibility |
| Observability | OTel + Prometheus + Grafana | Vendor-neutral, industry standard, rich ecosystem |

## Related Documents

- [Agent Design](agent-design.md)
- [Workflow Orchestration](workflow-orchestration.md)
- [Monitoring & Observability](monitoring-observability.md)
- [Deployment Guide](deployment-guide.md)
- [Architecture Decision Records](../adr/)
