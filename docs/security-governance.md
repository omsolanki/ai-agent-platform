# Security & AI Governance

## Governance Framework

Enterprise agentic AI systems require layered governance spanning input validation, execution controls, output sanitization, and audit compliance.

## Threat Model

| Threat | Vector | Impact | Mitigation |
|--------|--------|--------|------------|
| Prompt Injection | User input manipulation | Agent behavior override | Input scanning, system prompt isolation |
| Data Leakage | Agent output | PII/credential exposure | Output sanitization, PII detection |
| Tool Abuse | Agent tool calls | Unauthorized actions | Tool access controls, permission model |
| Hallucination | LLM generation | Misinformation | Grounding requirements, confidence thresholds |
| Cost Attack | High-volume requests | Budget exhaustion | Rate limiting, token budgets |
| Model Extraction | Repeated probing | IP theft | Output filtering, rate limiting |

## Input Governance

### Prompt Injection Protection

Detected patterns:
- "Ignore all/previous instructions"
- "You are now a [different role]"
- System prompt delimiter injection (`system:`)
- Script tag injection
- Known jailbreak patterns (DAN mode, etc.)

**Action**: Block request, log event, return governance rejection.

### PII Detection

Scanned patterns:
- Social Security Numbers (`\d{3}-\d{2}-\d{4}`)
- Credit card numbers (16 digits)
- Email addresses (warning only)

**Action**: Block or redact before agent processing.

### Content Moderation

Blocked topics:
- Malware generation
- Security bypass instructions
- Credential extraction requests

## Execution Governance

### Agent Permissions

| Agent | Allowed Tools | Data Access | Network |
|-------|--------------|-------------|---------|
| Research | Web search, document reader | Public sources, tenant docs | External APIs |
| Knowledge | Vector search, metadata query | Tenant knowledge base | Internal only |
| Summarization | None (LLM only) | Agent outputs only | LLM API only |

### Tool Access Controls

```python
TOOL_PERMISSIONS = {
    "research_agent": ["web_search", "document_reader"],
    "knowledge_agent": ["vector_search", "metadata_query"],
    "summarization_agent": [],  # No tools — synthesis only
}
```

### Token Budget Enforcement

- Per-request budget: 8,000 tokens (configurable)
- Per-tenant daily budget: configurable
- Enforcement at orchestration layer before agent dispatch

## Output Governance

### Hallucination Mitigation

1. **Grounding requirement**: Knowledge agent must cite sources
2. **Confidence thresholds**: Flag responses below 0.5 confidence
3. **Cross-validation**: Research and knowledge outputs compared for consistency
4. **Refusal training**: Agents instructed to refuse when context insufficient

### Output Sanitization

```python
def sanitize_output(text):
    # Redact SSN, credit cards
    # Remove system prompt fragments
    # Strip internal metadata
    return sanitized_text
```

## Human-in-the-Loop (HITL)

### Escalation Triggers

| Condition | Action |
|-----------|--------|
| Confidence < 0.5 | Queue for human review |
| Governance flag | Block and notify security team |
| High-value decision | Require approval before delivery |
| User explicit request | Route to human agent |

### HITL Workflow (Future)

![Human-in-the-Loop Workflow](../diagrams/governance-hitl.svg)

*Source: [governance-hitl.d2](../diagrams/governance-hitl.d2)*

## Audit Logging

Every governance event is logged to PostgreSQL:

```json
{
  "id": "uuid",
  "timestamp": "2025-06-07T10:30:00Z",
  "event_type": "governance_blocked",
  "actor": "governance_guard",
  "request_id": "abc-123",
  "details": {
    "reason": "Potential prompt injection detected",
    "severity": "critical",
    "pattern_matched": "ignore\\s+previous\\s+instructions"
  }
}
```

### Audit Events

| Event Type | Trigger |
|-----------|---------|
| `request_received` | API request accepted |
| `governance_blocked` | Input validation failed |
| `agent_executed` | Agent completed execution |
| `workflow_completed` | Full pipeline finished |
| `token_budget_exceeded` | Budget limit hit |
| `hitl_escalated` | Human review requested |

## Responsible AI Practices

1. **Transparency**: Confidence scores and citations included in every response
2. **Accountability**: Full audit trail from request to response
3. **Fairness**: No demographic bias in agent routing or model selection
4. **Privacy**: PII detection and redaction by default
5. **Safety**: Blocked topics and injection protection enabled by default
6. **Human oversight**: HITL escalation for low-confidence outputs

## Compliance Considerations

| Regulation | Requirement | Implementation |
|-----------|-------------|----------------|
| GDPR | Data minimization, right to deletion | Session TTL, data purge API |
| SOC 2 | Audit logging, access controls | PostgreSQL audit log, RBAC |
| HIPAA | PHI protection | PII detection, encryption at rest |
| EU AI Act | Transparency, human oversight | Confidence scores, HITL workflow |

## Security Hardening Checklist

- [ ] API authentication (JWT/OAuth2)
- [ ] TLS everywhere (API, DB, vector store)
- [ ] Secrets in vault (not environment variables in production)
- [ ] Network segmentation (agents in private subnet)
- [ ] Input validation on all endpoints
- [ ] Rate limiting per tenant
- [ ] Regular penetration testing
- [ ] Dependency vulnerability scanning
