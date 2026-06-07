"""Evaluation metric calculators."""

from app.models.schemas import EvaluationScorecard, FinalResponse


def calculate_task_completion(response: FinalResponse) -> float:
    """Score based on presence of expected outputs."""
    checks = [
        response.executive_summary is not None,
        bool(response.executive_summary.key_insights),
        response.status.value == "completed",
    ]
    if response.research_findings:
        checks.append(bool(response.research_findings.findings))
    if response.grounded_response:
        checks.append(bool(response.grounded_response.answer))
    return sum(checks) / len(checks)


def calculate_groundedness(response: FinalResponse) -> float:
    """Score based on citation coverage and retrieval quality."""
    if not response.grounded_response:
        return 0.5
    gr = response.grounded_response
    citation_score = min(1.0, len(gr.citations) / 3)
    confidence_score = gr.confidence.score
    retrieval_score = min(1.0, gr.retrieved_chunks / 5)
    return (citation_score + confidence_score + retrieval_score) / 3


def calculate_hallucination_rate(response: FinalResponse) -> float:
    """Estimate hallucination risk (lower confidence = higher risk)."""
    scores = []
    if response.grounded_response:
        scores.append(1.0 - response.grounded_response.confidence.score)
    if response.research_findings:
        scores.append(1.0 - response.research_findings.confidence.score)
    return sum(scores) / len(scores) if scores else 0.3


def calculate_agent_accuracy(response: FinalResponse) -> float:
    """Score based on agent success rate."""
    if not response.agent_outputs:
        return 0.0
    successes = sum(1 for o in response.agent_outputs if o.success)
    return successes / len(response.agent_outputs)


def calculate_cost_efficiency(response: FinalResponse) -> float:
    """Score cost efficiency (lower cost with good output = higher score)."""
    if response.total_cost_usd <= 0:
        return 1.0
    quality = calculate_task_completion(response)
    cost_factor = min(1.0, 0.01 / max(response.total_cost_usd, 0.001))
    return min(1.0, quality * cost_factor)


def build_scorecard(response: FinalResponse) -> EvaluationScorecard:
    """Build complete evaluation scorecard from workflow response."""
    task_completion = calculate_task_completion(response)
    groundedness = calculate_groundedness(response)
    hallucination = calculate_hallucination_rate(response)
    agent_accuracy = calculate_agent_accuracy(response)
    cost_efficiency = calculate_cost_efficiency(response)

    return EvaluationScorecard(
        request_id=response.request_id,
        task_completion=round(task_completion, 3),
        answer_quality=round((task_completion + groundedness) / 2, 3),
        groundedness=round(groundedness, 3),
        hallucination_rate=round(hallucination, 3),
        agent_accuracy=round(agent_accuracy, 3),
        workflow_success=response.status.value == "completed",
        latency_ms=response.total_latency_ms,
        cost_usd=response.total_cost_usd,
        cost_efficiency=round(cost_efficiency, 3),
    )
