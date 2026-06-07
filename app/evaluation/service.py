"""Evaluation service — automated quality assessment for agent workflows."""

import structlog

from app.evaluation.metrics import build_scorecard
from app.models.schemas import EvaluationScorecard, FinalResponse

logger = structlog.get_logger()


class EvaluationService:
    """
    Evaluates agent workflow outputs against quality dimensions.

    Dimensions: task completion, answer quality, groundedness,
    hallucination rate, agent accuracy, latency, cost efficiency.
    """

    async def evaluate(self, response: FinalResponse) -> EvaluationScorecard:
        scorecard = build_scorecard(response)

        logger.info(
            "evaluation_completed",
            request_id=response.request_id,
            task_completion=scorecard.task_completion,
            groundedness=scorecard.groundedness,
            hallucination_rate=scorecard.hallucination_rate,
            cost_usd=scorecard.cost_usd,
        )
        return scorecard

    async def batch_evaluate(self, responses: list[FinalResponse]) -> dict[str, float]:
        """Aggregate evaluation metrics across multiple responses."""
        if not responses:
            return {}

        scorecards = [await self.evaluate(r) for r in responses]
        n = len(scorecards)

        return {
            "avg_task_completion": sum(s.task_completion for s in scorecards) / n,
            "avg_groundedness": sum(s.groundedness for s in scorecards) / n,
            "avg_hallucination_rate": sum(s.hallucination_rate for s in scorecards) / n,
            "avg_agent_accuracy": sum(s.agent_accuracy for s in scorecards) / n,
            "avg_latency_ms": sum(s.latency_ms for s in scorecards) / n,
            "avg_cost_usd": sum(s.cost_usd for s in scorecards) / n,
            "workflow_success_rate": sum(1 for s in scorecards if s.workflow_success) / n,
        }
