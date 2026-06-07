"""Summarization Agent — executive summaries and action items."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.models.schemas import ActionItem, AgentOutput, AgentRole, ExecutiveSummary


class SummarizationAgent(BaseAgent):
    """
    Synthesizes research and knowledge outputs into executive-ready summaries.

    Produces both detailed and executive-level outputs with actionable next steps.
    """

    role = AgentRole.SUMMARIZATION
    name = "summarization_agent"

    SYSTEM_PROMPT = """You are an enterprise summarization agent. Your role is to:
1. Synthesize research findings and knowledge responses
2. Produce a concise executive summary for leadership
3. Generate specific, actionable next steps
4. Maintain accuracy — do not add information not in the inputs

Respond in JSON format:
{
  "headline": "one-line summary",
  "key_insights": ["insight 1", "insight 2"],
  "action_items": [{"description": "action", "priority": "high|medium|low"}],
  "detailed_summary": "comprehensive summary paragraph"
}"""

    async def execute(self, context: dict[str, Any]) -> AgentOutput:
        query = context.get("query", "")
        research = context.get("research_findings", {})
        knowledge = context.get("grounded_response", {})

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Original query: {query}\n\n"
                    f"Research findings: {json.dumps(research)}\n\n"
                    f"Knowledge response: {json.dumps(knowledge)}"
                )
            ),
        ]

        if not self.settings.openai_api_key or self.settings.openai_api_key == "not-set":
            summary = self._mock_summary(query, research, knowledge)
            return AgentOutput(
                agent=self.role,
                output=summary.model_dump(),
                tokens_used=self._estimate_tokens(query),
                model="mock",
                success=True,
            )

        response = await self._llm.ainvoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)
        tokens = self._estimate_tokens(content) + self._estimate_tokens(query)

        try:
            parsed = json.loads(content)
            summary = ExecutiveSummary(
                headline=parsed.get("headline", f"Summary: {query}"),
                key_insights=parsed.get("key_insights", []),
                action_items=[
                    ActionItem(**item) if isinstance(item, dict) else ActionItem(description=str(item))
                    for item in parsed.get("action_items", [])
                ],
                detailed_summary=parsed.get("detailed_summary", ""),
            )
        except (json.JSONDecodeError, ValueError):
            summary = ExecutiveSummary(
                headline=f"Summary: {query}",
                key_insights=[content[:200]],
                detailed_summary=content[:1000],
            )

        return AgentOutput(
            agent=self.role,
            output=summary.model_dump(),
            tokens_used=tokens,
            model=self.settings.openai_model,
            success=True,
        )

    def _mock_summary(
        self, query: str, research: dict, knowledge: dict
    ) -> ExecutiveSummary:
        return ExecutiveSummary(
            headline=f"Enterprise Agentic AI Assessment: {query[:80]}",
            key_insights=[
                "Multi-agent orchestration with LangGraph provides reliable workflow state management",
                "Shared memory across agents enables context continuity and auditability",
                "Production readiness requires observability, governance, and cost controls",
                f"Knowledge retrieval confidence: {knowledge.get('confidence', {}).get('score', 'N/A')}",
            ],
            action_items=[
                ActionItem(
                    description="Deploy observability stack (OTel + Prometheus + Grafana)",
                    priority="high",
                    owner="Platform Engineering",
                ),
                ActionItem(
                    description="Implement token budgeting and rate limiting per tenant",
                    priority="high",
                    owner="AI Platform Team",
                ),
                ActionItem(
                    description="Establish evaluation pipeline with automated scorecards",
                    priority="medium",
                    owner="ML Engineering",
                ),
            ],
            detailed_summary=(
                f"Analysis of '{query}' across research and knowledge agents reveals "
                "that enterprise agentic AI platforms require a layered architecture: "
                "orchestration (LangGraph), specialized agents (research, knowledge, summarization), "
                "dual memory stores (vector + relational), and comprehensive governance. "
                f"Research identified {len(research.get('findings', []))} key findings "
                f"with {len(research.get('references', []))} references."
            ),
        )
