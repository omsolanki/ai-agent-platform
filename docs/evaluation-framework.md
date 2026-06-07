# Evaluation Framework

## Purpose

Non-deterministic AI systems require systematic evaluation to ensure quality, safety, and cost-effectiveness. This framework provides automated quality assessment for every agent workflow execution.

## Evaluation Dimensions

| Dimension | Weight | Measurement | Target |
|-----------|--------|-------------|--------|
| Task Completion | 20% | Output field presence and completeness | > 0.90 |
| Answer Quality | 20% | Composite of completion + groundedness | > 0.85 |
| Groundedness | 25% | Citation coverage + retrieval quality | > 0.80 |
| Hallucination Rate | 15% | Inverse confidence scores | < 0.15 |
| Agent Accuracy | 10% | Per-agent success rate | > 0.95 |
| Latency | 5% | End-to-end execution time | < 15s |
| Cost Efficiency | 5% | Quality per dollar spent | > 0.70 |

## Evaluation Pipeline

![Evaluation Framework](../diagrams/evaluation-flow.svg)

*Source: [evaluation-flow.d2](../diagrams/evaluation-flow.d2)*

## Scorecard Schema

```json
{
  "request_id": "abc-123",
  "task_completion": 0.95,
  "answer_quality": 0.88,
  "groundedness": 0.92,
  "hallucination_rate": 0.08,
  "agent_accuracy": 1.0,
  "workflow_success": true,
  "latency_ms": 3200,
  "cost_usd": 0.0015,
  "cost_efficiency": 0.85,
  "notes": ""
}
```

## Sample Scorecards

### High-Quality Execution

| Metric | Score | Assessment |
|--------|-------|------------|
| Task Completion | 1.00 | All outputs present |
| Groundedness | 0.92 | 5 citations, high retrieval |
| Hallucination Rate | 0.08 | Low risk |
| Agent Accuracy | 1.00 | All 3 agents succeeded |
| Cost Efficiency | 0.85 | Good quality per dollar |

### Degraded Execution

| Metric | Score | Assessment |
|--------|-------|------------|
| Task Completion | 0.67 | Missing knowledge response |
| Groundedness | 0.50 | No citations available |
| Hallucination Rate | 0.35 | Higher risk without grounding |
| Agent Accuracy | 0.67 | Knowledge agent failed |
| Cost Efficiency | 0.40 | Partial results at full cost |

## Metric Calculators

### Task Completion

```python
checks = [
    executive_summary exists,
    key_insights non-empty,
    status == completed,
    research findings present (if routed),
    grounded response present (if routed),
]
score = passed_checks / total_checks
```

### Groundedness

```python
citation_score = min(1.0, len(citations) / 3)
confidence_score = grounded_response.confidence.score
retrieval_score = min(1.0, retrieved_chunks / 5)
groundedness = mean(citation_score, confidence_score, retrieval_score)
```

### Hallucination Rate

```python
risk_scores = [1.0 - confidence for each agent output]
hallucination_rate = mean(risk_scores)
```

## Evaluation in CI/CD

```bash
# Run evaluation as part of deployment pipeline
pytest tests/test_workflow.py -v
python examples/run_workflow.py http://localhost:8000 "test query"

# Quality gates:
# - task_completion >= 0.90
# - agent_accuracy >= 0.95
# - hallucination_rate <= 0.20
```

## Continuous Improvement Loop

![Continuous Improvement Loop](../diagrams/evaluation-improvement.svg)

*Source: [evaluation-improvement.d2](../diagrams/evaluation-improvement.d2)*

## Future Enhancements

- **A/B testing**: Compare agent prompt versions with statistical significance
- **Regression detection**: Alert when metrics drop below rolling baseline
- **Benchmark suite**: Curated test queries with expected outputs
- **LLM-as-judge**: GPT-4 evaluation of response quality (sampled)
- **User feedback integration**: Thumbs up/down as evaluation signal
