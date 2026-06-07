# Agent Design

## Design Philosophy

Agents in this platform follow the **Single Responsibility Principle**. Each agent is a specialized, independently testable unit with a clearly defined input contract, output schema, and failure mode. Agents do not communicate directly — all interaction flows through the orchestration layer via shared workflow state.

## Agent Architecture Pattern

![BaseAgent Architecture](../diagrams/base-agent.svg)

*Source: [base-agent.d2](../diagrams/base-agent.d2)*

Multi-agent collaboration and shared memory:

![Agent Interaction Flow](../diagrams/agent-interaction.svg)

*Source: [agent-interaction.d2](../diagrams/agent-interaction.d2)*

Every agent inherits from `BaseAgent` which provides:
- OpenTelemetry span creation
- Prometheus metric recording
- Token estimation and cost tracking
- Standardized error handling and `AgentOutput` wrapping

## Agent Specifications

### 1. Research Agent

**Purpose**: Gather and structure information from available sources.

**Input Context**:
```json
{
  "query": "user question",
  "shared_memory": {
    "conversation_history": [],
    "user_context": {}
  }
}
```

**Output Schema** (`ResearchFinding`):
```json
{
  "topic": "identified research topic",
  "findings": ["structured finding 1", "finding 2"],
  "references": ["source 1", "source 2"],
  "confidence": {
    "score": 0.82,
    "rationale": "Multiple authoritative sources",
    "source_count": 3
  }
}
```

**Production Extensions**:
- Web search API integration (Tavily, SerpAPI, Bing)
- Document ingestion pipeline (PDF, DOCX, HTML)
- Enterprise connector framework (SharePoint, Confluence, Jira)
- Source credibility scoring

**Failure Modes**:
- No sources found → Return low-confidence finding with rationale
- API timeout → Retry with exponential backoff
- Rate limited → Queue and retry

---

### 2. Knowledge Agent

**Purpose**: Retrieve relevant knowledge and generate grounded, cited responses.

**Input Context**:
```json
{
  "query": "user question",
  "research_findings": { "...ResearchFinding" },
  "shared_memory": { "...shared context" }
}
```

**Output Schema** (`GroundedResponse`):
```json
{
  "answer": "grounded answer with citations",
  "citations": ["platform-docs/governance", "kb-003"],
  "confidence": {
    "score": 0.88,
    "rationale": "5 relevant chunks retrieved",
    "source_count": 5
  },
  "retrieved_chunks": 5
}
```

**Retrieval Pipeline**:
1. Query embedding generation
2. Qdrant vector similarity search (top-k)
3. Metadata filtering (category, version, tenant)
4. Context assembly with research findings
5. LLM generation with citation requirements

**Production Extensions**:
- Hybrid search (vector + BM25)
- Re-ranking with cross-encoder models
- Chunk deduplication and context window optimization
- Multi-collection search across tenant knowledge bases

---

### 3. Summarization Agent

**Purpose**: Synthesize multi-agent outputs into executive-ready deliverables.

**Input Context**:
```json
{
  "query": "original user question",
  "research_findings": { "...ResearchFinding" },
  "grounded_response": { "...GroundedResponse" }
}
```

**Output Schema** (`ExecutiveSummary`):
```json
{
  "headline": "one-line executive summary",
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "action_items": [
    {
      "description": "Deploy observability stack",
      "priority": "high",
      "owner": "Platform Engineering"
    }
  ],
  "detailed_summary": "comprehensive multi-paragraph summary"
}
```

**Design Constraints**:
- Must not hallucinate — only synthesize provided inputs
- Action items must be specific and assignable
- Executive summary must be readable in < 30 seconds

## Agent Communication Model

Agents never call each other directly. Communication is **mediated through workflow state**:

![Agent State Communication](../diagrams/agent-state-flow.svg)

*Source: [agent-state-flow.d2](../diagrams/agent-state-flow.d2)*

## Agent Selection & Routing

The `AgentRouter` determines which agents execute based on:

| Factor | Impact |
|--------|--------|
| Request feature flags | `enable_research`, `enable_knowledge`, `enable_summarization` |
| Query complexity | Long queries may skip research for cost savings |
| Cost budget | Low budget routes to fewer agents |
| Session context | Returning sessions may skip research if context exists |

Available routes:
- **Full Pipeline**: Research → Knowledge → Summarization
- **Knowledge Only**: Knowledge → Summarization
- **Research + Summary**: Research → Summarization
- **Direct Summary**: Summarization only

## Testing Strategy

Each agent is independently testable:

```python
agent = ResearchAgent()
output = await agent.run({"query": "test query"})
assert output.success
assert output.output["findings"]
```

Mock mode (no API key) provides deterministic outputs for CI/CD pipelines.

## Future Agent Extensions

| Agent | Purpose | Priority |
|-------|---------|----------|
| Code Agent | Code generation, review, execution | High |
| Data Agent | SQL generation, data analysis | High |
| Planning Agent | Task decomposition, workflow planning | Medium |
| Review Agent | Output quality validation, fact-checking | Medium |
| Human-in-the-Loop Agent | Escalation and approval workflows | Medium |
