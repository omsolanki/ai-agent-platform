"""Research Agent — web/document research and context preparation."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.models.schemas import AgentOutput, AgentRole, ConfidenceIndicator, ResearchFinding


class ResearchAgent(BaseAgent):
    """
    Gathers and structures information from available sources.

    In production, this agent would integrate with web search APIs,
    document parsers, and enterprise knowledge connectors.
    """

    role = AgentRole.RESEARCH
    name = "research_agent"

    SYSTEM_PROMPT = """You are an enterprise research agent. Your role is to:
1. Analyze the user's query and identify key research areas
2. Gather relevant information from provided context and knowledge
3. Structure findings with clear references
4. Provide confidence indicators based on source quality

Respond in JSON format:
{
  "topic": "research topic",
  "findings": ["finding 1", "finding 2"],
  "references": ["source 1", "source 2"],
  "confidence_score": 0.0-1.0,
  "confidence_rationale": "why this confidence level"
}"""

    async def execute(self, context: dict[str, Any]) -> AgentOutput:
        query = context.get("query", "")
        shared_memory = context.get("shared_memory", {})
        prior_context = shared_memory.get("conversation_history", [])

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(
                content=f"Query: {query}\n\nPrior context: {json.dumps(prior_context)}"
            ),
        ]

        if not self.settings.openai_api_key or self.settings.openai_api_key == "not-set":
            finding = self._mock_research(query)
            return AgentOutput(
                agent=self.role,
                output=finding.model_dump(),
                tokens_used=self._estimate_tokens(query),
                model="mock",
                success=True,
            )

        response = await self._llm.ainvoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)
        tokens = self._estimate_tokens(content) + self._estimate_tokens(query)

        try:
            parsed = json.loads(content)
            finding = ResearchFinding(
                topic=parsed.get("topic", query),
                findings=parsed.get("findings", []),
                references=parsed.get("references", []),
                confidence=ConfidenceIndicator(
                    score=float(parsed.get("confidence_score", 0.7)),
                    rationale=parsed.get("confidence_rationale", ""),
                    source_count=len(parsed.get("references", [])),
                ),
            )
        except (json.JSONDecodeError, ValueError):
            finding = ResearchFinding(
                topic=query,
                findings=[content[:500]],
                references=["llm-synthesis"],
                confidence=ConfidenceIndicator(score=0.6, rationale="Unstructured LLM output"),
            )

        return AgentOutput(
            agent=self.role,
            output=finding.model_dump(),
            tokens_used=tokens,
            model=self.settings.openai_model,
            success=True,
        )

    def _mock_research(self, query: str) -> ResearchFinding:
        """Deterministic output for demo/CI without API keys."""
        return ResearchFinding(
            topic=query,
            findings=[
                f"Enterprise agentic AI platforms require orchestration layers for multi-agent coordination.",
                f"Research on '{query}' indicates growing adoption of LangGraph for workflow state management.",
                "Governance, observability, and cost control are critical production requirements.",
            ],
            references=[
                "Gartner: Agentic AI Market Guide 2025",
                "LangGraph Documentation — State Management",
                "OpenAI: Best Practices for Production LLM Systems",
            ],
            confidence=ConfidenceIndicator(
                score=0.82,
                rationale="Multiple authoritative sources with consistent findings",
                source_count=3,
            ),
        )
