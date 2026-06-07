# AI Agent Platform

> Enterprise-grade Agentic AI reference implementation — demonstrating how multi-agent systems are designed, orchestrated, monitored, governed, and deployed.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-purple.svg)](https://langchain-ai.github.io/langgraph/)

**This is not a chatbot.** This is an architecture showcase for Principal Engineers, AI Platform Architects, and Heads of Engineering building production agentic AI systems.

---

## Executive Summary

Organizations adopting agentic AI face a common challenge: how to move from prototype chatbots to governed, observable, cost-controlled multi-agent platforms. This repository provides a **reference implementation** that demonstrates the architectural patterns, design decisions, and operational practices required for enterprise deployment.

The platform orchestrates three specialized agents — Research, Knowledge, and Summarization — through a LangGraph workflow engine with shared memory, governance guards, observability instrumentation, and automated evaluation.

## Business Problem

| Challenge | How This Platform Addresses It |
|-----------|-------------------------------|
| Unpredictable AI costs | Token budgeting, model tiering, cost estimation per request |
| No visibility into agent behavior | OpenTelemetry traces, Prometheus metrics, structured audit logs |
| Quality inconsistency | Automated evaluation scorecards with groundedness and hallucination metrics |
| Security and compliance gaps | Prompt injection detection, PII filtering, audit logging, governance guards |
| Architecture uncertainty | Documented ADRs, tradeoff analysis, 4-stage scalability evolution |
| Vendor lock-in risk | Vendor-neutral observability, abstraction layers, self-hosted options |

## Why Agentic AI

Traditional LLM applications follow a single-prompt pattern: input → LLM → output. Agentic AI decomposes complex tasks into specialized agents that collaborate through orchestrated workflows:

```
Single LLM:     User → [One Model] → Response (limited, expensive, ungoverned)

Agentic AI:     User → [Router] → [Research] → [Knowledge] → [Summarization] → Response
                                   ↑ governed, observable, cost-controlled ↑
```

**Benefits**: Specialized quality per task, cost optimization via routing, governance at every step, observable and debuggable execution, independently scalable agents.

## Architecture Overview

```
┌─────────────┐     ┌──────────────────────────────────────────────────┐
│   Client    │────▶│              AI Agent Platform                  │
│  (API/UI)   │     │                                                  │
└─────────────┘     │  ┌─────────┐  ┌──────────┐  ┌──────────────┐  │
                    │  │ FastAPI │─▶│ LangGraph │─▶│  Agent Pool  │  │
                    │  │   API   │  │ Workflow  │  │  (3 agents)  │  │
                    │  └─────────┘  └──────────┘  └──────────────┘  │
                    │       │              │              │          │
                    │  ┌─────────┐  ┌──────────┐  ┌──────────────┐  │
                    │  │Governance│  │  Memory  │  │Observability │  │
                    │  └─────────┘  └──────────┘  └──────────────┘  │
                    └──────────────────────────────────────────────────┘
                              │                    │
                    ┌─────────┴──────┐    ┌───────┴────────┐
                    │  Qdrant + PG   │    │   OpenAI API   │
                    └────────────────┘    └────────────────┘
```

See [docs/architecture.md](docs/architecture.md) for the complete system architecture.

## Agent Design

Three collaborating agents, each with a single responsibility:

### Research Agent
Gathers and structures information from available sources.
- **Outputs**: Structured findings, references, confidence indicators
- **Model**: gpt-4o-mini

### Knowledge Agent
Retrieves relevant knowledge via vector search and generates grounded, cited responses.
- **Outputs**: Grounded answers, citations, confidence scores
- **Model**: gpt-4o-mini + Qdrant retrieval

### Summarization Agent
Synthesizes multi-agent outputs into executive-ready deliverables.
- **Outputs**: Executive summary, key insights, action items
- **Model**: gpt-4o-mini

See [docs/agent-design.md](docs/agent-design.md) for detailed agent specifications.

## Workflow Orchestration

```
User Request → Governance Guard → Agent Router → Research → Knowledge → Summarization → Evaluation → Response
```

| Capability | Implementation |
|-----------|---------------|
| Agent communication | Shared LangGraph workflow state |
| Context passing | Structured context dict per agent |
| State management | Immutable state updates per node |
| Retry handling | Exponential backoff, max 3 retries |
| Failure recovery | Graceful degradation, partial results |
| Cost estimation | Pre-execution cost projection |

See [docs/workflow-orchestration.md](docs/workflow-orchestration.md) for the complete orchestration design.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for full stack)
- Optional: OpenAI API key

### Local Development (No Docker)

```bash
git clone https://github.com/your-org/ai-agent-platform.git
cd ai-agent-platform

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Works without API key (mock mode)
uvicorn app.api.main:app --reload --port 8000
```

### Full Stack (Docker)

```bash
cp .env.example .env
cd docker && docker-compose up -d

# Verify
curl http://localhost:8000/api/v1/health

# Run example workflow
python ../examples/run_workflow.py
```

### API Usage

```bash
# Execute workflow
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "How should we design an enterprise multi-agent AI platform?"}'

# Estimate cost before execution
curl -X POST http://localhost:8000/api/v1/workflow/estimate-cost \
  -H "Content-Type: application/json" \
  -d '{"query": "Enterprise AI governance best practices"}'

# Get evaluation scorecard
curl -X POST http://localhost:8000/api/v1/workflow/evaluate \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the key components of agentic AI observability?"}'
```

API documentation available at `http://localhost:8000/docs`.

## Memory Design

| Tier | Store | Retention | Purpose |
|------|-------|-----------|---------|
| Short-term | LangGraph state | Request lifetime | Conversation context, agent outputs |
| Vector | Qdrant | Permanent | Semantic knowledge retrieval |
| Metadata | PostgreSQL | 90 days | Sessions, workflows, audit logs |
| Cache | Redis (Stage 2+) | 1 hour | Frequent query caching |

See [docs/architecture.md](docs/architecture.md) and [diagrams/memory-architecture.d2](diagrams/memory-architecture.d2).

## Observability

| Pillar | Technology | What's Tracked |
|--------|-----------|----------------|
| Traces | OpenTelemetry | Per-agent spans, LLM calls, retrieval |
| Metrics | Prometheus | Latency, tokens, cost, failure rates |
| Logs | structlog (JSON) | Workflow events, governance blocks |
| Dashboards | Grafana | Platform overview, agent performance, cost |

```bash
# Prometheus metrics
curl http://localhost:8000/api/v1/metrics

# Grafana dashboards
open http://localhost:3000  # admin/admin
```

See [docs/monitoring-observability.md](docs/monitoring-observability.md).

## Cost Governance

| Strategy | Impact |
|----------|--------|
| Model tiering (gpt-4o-mini default) | 90% cost reduction vs gpt-4o |
| Agent routing (skip unnecessary agents) | 30-60% savings on simple queries |
| Token budgeting (8K per request) | Prevents runaway costs |
| Response caching (40% hit rate) | 40% reduction at scale |
| Pre-execution cost estimation | Transparent cost before execution |

**Estimated cost per workflow**: ~$0.001 (full pipeline, gpt-4o-mini)

See [docs/cost-governance.md](docs/cost-governance.md) for detailed calculations.

## Evaluation Framework

Every workflow execution produces an automated quality scorecard:

| Dimension | Target | Measurement |
|-----------|--------|-------------|
| Task Completion | > 0.90 | Output completeness |
| Groundedness | > 0.80 | Citation + retrieval quality |
| Hallucination Rate | < 0.15 | Inverse confidence |
| Agent Accuracy | > 0.95 | Per-agent success rate |
| Cost Efficiency | > 0.70 | Quality per dollar |

See [docs/evaluation-framework.md](docs/evaluation-framework.md).

## AI Governance

- **Prompt injection protection** — Pattern-based input scanning
- **PII detection** — SSN, credit card, email filtering
- **Tool access controls** — Per-agent permission model
- **Token budget enforcement** — Configurable per-request limits
- **Audit logging** — Every governance event persisted
- **Hallucination mitigation** — Grounding requirements, confidence thresholds

See [docs/security-governance.md](docs/security-governance.md).

## Deployment Options

| Model | Use Case | Guide |
|-------|----------|-------|
| Local Docker | Development, demos | [deployment-local.d2](diagrams/deployment-local.d2) |
| AWS ECS/Fargate | Production SaaS | [deployment-aws.d2](diagrams/deployment-aws.d2) |
| Kubernetes/EKS | Enterprise multi-tenant | [deployment-k8s.d2](diagrams/deployment-k8s.d2) |

See [docs/deployment-guide.md](docs/deployment-guide.md).

## Scalability Evolution

```
Stage 1: Single Agent Runtime     ← You are here
Stage 2: Distributed Agent Services
Stage 3: Dedicated Memory Layer
Stage 4: Enterprise Multi-Agent Platform
```

See [docs/tradeoffs.md](docs/tradeoffs.md) for the complete evolution model.

## Design Decisions

| ADR | Decision | Rationale |
|-----|----------|-----------|
| [ADR-001](adr/adr-001-agent-framework.md) | LangGraph for orchestration | AI-native state management, graph workflows |
| [ADR-002](adr/adr-002-memory-strategy.md) | Qdrant + PostgreSQL dual store | Optimal per access pattern |
| [ADR-003](adr/adr-003-routing-strategy.md) | Rule-based agent router | Zero-cost, deterministic routing |
| [ADR-004](adr/adr-004-model-selection.md) | Tiered model selection | 90% cost reduction |
| [ADR-005](adr/adr-005-observability.md) | OTel + Prometheus + Grafana | Vendor-neutral observability |

## Repository Structure

```
ai-agent-platform/
├── README.md                          # This file
├── docs/                              # Architecture documentation
│   ├── architecture.md                # System architecture
│   ├── agent-design.md                # Agent specifications
│   ├── workflow-orchestration.md      # Orchestration design
│   ├── monitoring-observability.md    # Observability framework
│   ├── cost-governance.md             # Cost control strategy
│   ├── evaluation-framework.md        # Quality evaluation
│   ├── security-governance.md         # AI governance
│   ├── deployment-guide.md            # Deployment models
│   └── tradeoffs.md                   # Tradeoffs & evolution
├── diagrams/                          # D2 architecture diagrams (SVG + local icons)
├── adr/                               # Architecture Decision Records
├── app/                               # Python implementation
│   ├── agents/                        # Research, Knowledge, Summarization
│   ├── orchestration/                 # Router, workflow engine, retry
│   ├── memory/                        # Vector + metadata stores
│   ├── evaluation/                    # Quality scorecards
│   ├── monitoring/                    # OTel + Prometheus
│   ├── governance/                    # Security guards
│   └── api/                           # FastAPI endpoints
├── docker/                            # Docker Compose + configs
├── examples/                          # Usage examples
└── tests/                             # Integration tests
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI |
| Orchestration | LangGraph |
| LLM | OpenAI (gpt-4o-mini) |
| Vector Store | Qdrant |
| Metadata Store | PostgreSQL |
| Observability | OpenTelemetry, Prometheus, Grafana |
| Containerization | Docker |

## Future Enhancements

- [ ] LangGraph checkpointing for human-in-the-loop workflows
- [ ] Redis caching layer (Stage 2)
- [ ] LLM-as-judge evaluation (sampled quality assessment)
- [ ] Multi-provider LLM support (Anthropic, Google)
- [ ] Agent marketplace for custom agent registration (Stage 4)
- [ ] Per-tenant governance policies and cost budgets
- [ ] Web search integration for Research Agent
- [ ] Hybrid search (vector + BM25) for Knowledge Agent

## Architecture Diagrams

Diagrams use **local SVG icons** (no CDN dependency) with a shared D2 theme, color-coded layers, and labeled connectors.

```bash
# Requires D2 CLI: https://d2lang.com/
make diagrams
```

Rendered outputs: `diagrams/*.svg` and `diagrams/*.pdf` (19 architecture diagrams). SVGs are embedded in `docs/`.

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## License

MIT

---

*Built to demonstrate enterprise agentic AI architecture — not as a product, but as a reference for engineering leaders designing the next generation of AI platforms.*
