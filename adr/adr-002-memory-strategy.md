# ADR-002: Memory Strategy

## Status

Accepted

## Date

2025-06-07

## Context

Agentic AI systems require both short-term context (conversation state, agent outputs) and long-term knowledge (semantic retrieval, metadata, audit trails). The memory architecture must support multiple access patterns with different consistency and latency requirements.

## Decision Drivers

- Sub-100ms retrieval for agent context
- Semantic search over knowledge base
- ACID compliance for audit and workflow metadata
- Independent scaling of vector vs relational workloads
- Data sovereignty (self-hosted option)

## Alternatives Considered

### 1. Dual Store: Qdrant + PostgreSQL (Selected)

**Pros**: Purpose-built for each access pattern, independent scaling, mature ecosystems, self-hosted option.

**Cons**: Operational complexity of two databases, no unified query interface.

### 2. PostgreSQL with pgvector

**Pros**: Single database, ACID for everything, simpler operations.

**Cons**: Vector search performance degrades at scale, mixed workloads compete for resources.

### 3. Redis-only

**Pros**: Extremely fast, simple, good for short-term memory.

**Cons**: No semantic search, limited persistence, not suitable for audit trails.

### 4. Pinecone + PostgreSQL

**Pros**: Managed vector search, zero-ops, excellent performance.

**Cons**: Vendor lock-in, per-vector pricing at scale, data leaves your infrastructure.

## Decision

**Dual-store architecture**: Qdrant for vector memory, PostgreSQL for metadata/audit, in-process dict for short-term context.

## Memory Tiers

| Tier | Store | Retention | Access Pattern |
|------|-------|-----------|----------------|
| Short-term | LangGraph state | Request lifetime | Read/write per agent |
| Vector | Qdrant | Permanent (with TTL option) | Semantic search |
| Metadata | PostgreSQL | 90 days (configurable) | CRUD + audit queries |
| Cache | Redis (Stage 2+) | 1 hour | Key-value lookup |

## Consequences

### Positive
- Optimal performance per access pattern
- Independent scaling and backup strategies
- Clear data ownership boundaries

### Negative
- Two databases to operate and monitor
- Cross-store queries require application-level joins
- In-memory fallback needed for local development

## Future Evolution

- Add Redis caching layer (Stage 2)
- Implement embedding pipeline for knowledge ingestion
- Evaluate unified stores if pgvector performance improves
- Add memory service abstraction for Stage 3
