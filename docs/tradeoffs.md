# Architecture Tradeoffs & Evolution

## Design Tradeoffs

### LangGraph vs Temporal

| Factor | LangGraph | Temporal |
|--------|-----------|----------|
| LLM-native state | Excellent | Requires custom integration |
| Learning curve | Low (Python) | High (new paradigm) |
| Durability | Checkpointing (basic) | Built-in (excellent) |
| Ecosystem | AI-focused | General workflow |
| **Decision** | LangGraph for AI workflows | Temporal for business process orchestration |

### Qdrant vs Pinecone

| Factor | Qdrant | Pinecone |
|--------|--------|----------|
| Hosting | Self-hosted or cloud | Managed only |
| Cost | Infrastructure cost | Per-vector pricing |
| Filtering | Rich payload filtering | Metadata filtering |
| Performance | Excellent at scale | Excellent at scale |
| **Decision** | Qdrant for cost control and data sovereignty | Pinecone for zero-ops managed |

### Single Process vs Microservices

| Factor | Single Process | Microservices |
|--------|---------------|---------------|
| Complexity | Low | High |
| Scalability | Vertical | Horizontal per agent |
| Latency | Low (in-process) | Higher (network) |
| Deployment | Simple | Independent deploys |
| **Decision** | Single process for Stage 1-2 | Microservices for Stage 3-4 |

### Mock Mode vs API-Required

| Factor | Mock Mode | API Required |
|--------|-----------|-------------|
| CI/CD | Works without keys | Requires secrets management |
| Demo quality | Deterministic | Non-deterministic |
| Development | Fast iteration | Real behavior |
| **Decision** | Mock fallback when no API key | Production uses real API |

## Scalability Evolution

![Scalability Evolution](../diagrams/scaling-evolution.svg)

*Source: [scaling-evolution.d2](../diagrams/scaling-evolution.d2)*

### Stage 1: Single Agent Runtime (Current)

**Characteristics**:
- All components in one Python process
- In-memory fallbacks for Qdrant and PostgreSQL
- Suitable for: Development, demos, < 100 req/day
- Limitations: No horizontal scaling, no persistence

**When to move to Stage 2**: > 100 concurrent requests, need persistence, multi-developer team

---

### Stage 2: Distributed Agent Services

**Characteristics**:
- API gateway decoupled from agent execution
- Each agent type runs as independent service
- Message queue for async agent communication
- Suitable for: 1K-10K req/day, team of 5-10

**Key changes**:
- Extract agents into separate FastAPI services
- Add Redis for shared state and caching
- Deploy PostgreSQL and Qdrant as managed services

---

### Stage 3: Dedicated Memory Layer

**Characteristics**:
- Dedicated memory service with read replicas
- Redis caching layer (L1/L2)
- Qdrant cluster with sharding
- PostgreSQL with read replicas for audit queries
- Suitable for: 10K-100K req/day, multi-tenant

**Key changes**:
- Memory service as standalone gRPC/REST service
- Embedding pipeline for knowledge ingestion
- Session management with TTL and cleanup jobs

---

### Stage 4: Enterprise Multi-Agent Platform

**Characteristics**:
- Multi-tenant with isolated knowledge bases
- Agent marketplace for custom agent registration
- Policy engine for governance rules per tenant
- Cost management with per-tenant budgets
- Suitable for: 100K+ req/day, enterprise customers

**Key changes**:
- Control plane / data plane separation
- Agent SDK for third-party agent development
- Per-tenant configuration and model selection
- SLA monitoring and billing integration

## Migration Path

The migration timeline is shown at the bottom of the [scaling evolution diagram](../diagrams/scaling-evolution.svg): Stage 1 → Stage 2 (3–6 mo) → Stage 3 (6–12 mo) → Stage 4 (12+ mo).

Each stage is independently valuable — there is no requirement to reach Stage 4. Most organizations find Stage 2-3 sufficient for production workloads.

## Cost Evolution

| Stage | Infra Cost/Month | Per-Request Cost | Break-even Volume |
|-------|-----------------|------------------|-------------------|
| Stage 1 | ~$0 (local) | $0.001 | N/A |
| Stage 2 | ~$500 | $0.001 | 500K req/month |
| Stage 3 | ~$2,000 | $0.0008 | 2.5M req/month |
| Stage 4 | ~$10,000+ | $0.0005 | 20M+ req/month |

Economies of scale come from caching, model tiering, and shared infrastructure — not from architectural complexity alone.
