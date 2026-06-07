# ADR-001: Agent Framework Selection

## Status

Accepted

## Date

2025-06-07

## Context

The platform requires an orchestration framework for multi-agent workflows with state management, retry handling, and conditional routing. The framework must integrate with LangChain for LLM interactions and support Python-native development.

## Decision Drivers

- Native LLM/AI workflow support
- Stateful graph-based execution
- Python ecosystem compatibility
- Checkpointing and human-in-the-loop support
- Community adoption and documentation quality
- Production readiness

## Alternatives Considered

### 1. LangGraph (Selected)

**Pros**: Native LangChain integration, graph-based state management, checkpointing, conditional edges, growing enterprise adoption, Python-native.

**Cons**: Relatively new, smaller community than Celery/Temporal, checkpointing still maturing.

### 2. Temporal

**Pros**: Battle-tested durability, excellent failure recovery, strong observability, language-agnostic.

**Cons**: Significant operational overhead, not LLM-native, steep learning curve, overkill for AI-specific workflows.

### 3. Celery + Custom State

**Pros**: Mature, well-understood, large community, flexible.

**Cons**: No native state management, requires custom orchestration logic, not designed for AI workflows.

### 4. Raw Async/Await

**Pros**: Maximum control, no dependencies, simple.

**Cons**: No graph semantics, manual state management, no checkpointing, difficult to maintain.

## Decision

**LangGraph** for workflow orchestration with LangChain for LLM interactions.

## Rationale

LangGraph provides the best balance of AI-native features and production capabilities. Its graph-based model maps directly to our agent interaction patterns, and native state management eliminates the need for custom context-passing infrastructure.

## Consequences

### Positive
- Rapid development of multi-agent workflows
- Native state passing between agents
- Future checkpointing and HITL support
- Strong LangChain ecosystem integration

### Negative
- Framework maturity risk (mitigated by LangChain backing)
- Team must learn graph-based workflow patterns
- Limited production case studies compared to Temporal

## Future Evolution

- Evaluate Temporal for long-running business process integration
- Add LangGraph checkpointing when human-in-the-loop is required
- Monitor LangGraph Server for managed deployment option
