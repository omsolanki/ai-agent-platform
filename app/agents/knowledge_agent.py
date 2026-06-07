"""Knowledge Agent — vector retrieval, context enrichment, grounded answers."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.memory.service import MemoryService
from app.models.schemas import AgentOutput, AgentRole, ConfidenceIndicator, GroundedResponse


class KnowledgeAgent(BaseAgent):
    """
    Retrieves relevant knowledge from vector store and generates grounded responses.

    Integrates with Qdrant for semantic search and PostgreSQL for metadata.
    """

    role = AgentRole.KNOWLEDGE
    name = "knowledge_agent"

    SYSTEM_PROMPT = """You are an enterprise knowledge agent. Your role is to:
1. Use retrieved context to answer questions accurately
2. Cite sources for every claim
3. Indicate confidence based on retrieval quality
4. Refuse to answer when context is insufficient

Respond in JSON format:
{
  "answer": "grounded answer",
  "citations": ["source 1", "source 2"],
  "confidence_score": 0.0-1.0,
  "confidence_rationale": "why this confidence level"
}"""

    def __init__(self, memory_service: MemoryService | None = None, **kwargs):
        super().__init__(**kwargs)
        self.memory = memory_service or MemoryService(self.settings)

    async def execute(self, context: dict[str, Any]) -> AgentOutput:
        query = context.get("query", "")
        research = context.get("research_findings", {})
        research_context = json.dumps(research) if research else ""

        retrieved = await self.memory.search(query, limit=5)
        retrieval_context = "\n".join(
            f"[{r['source']}] {r['content']}" for r in retrieved
        )

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Query: {query}\n\n"
                    f"Research context: {research_context}\n\n"
                    f"Retrieved knowledge:\n{retrieval_context}"
                )
            ),
        ]

        if not self.settings.openai_api_key or self.settings.openai_api_key == "not-set":
            response = self._mock_knowledge(query, retrieved)
            return AgentOutput(
                agent=self.role,
                output=response.model_dump(),
                tokens_used=self._estimate_tokens(query),
                model="mock",
                success=True,
            )

        llm_response = await self._llm.ainvoke(messages)
        content = (
            llm_response.content
            if isinstance(llm_response.content, str)
            else str(llm_response.content)
        )
        tokens = self._estimate_tokens(content) + self._estimate_tokens(query)

        try:
            parsed = json.loads(content)
            grounded = GroundedResponse(
                answer=parsed.get("answer", content),
                citations=parsed.get("citations", [r["source"] for r in retrieved]),
                confidence=ConfidenceIndicator(
                    score=float(parsed.get("confidence_score", 0.75)),
                    rationale=parsed.get("confidence_rationale", ""),
                    source_count=len(retrieved),
                ),
                retrieved_chunks=len(retrieved),
            )
        except (json.JSONDecodeError, ValueError):
            grounded = GroundedResponse(
                answer=content[:1000],
                citations=[r["source"] for r in retrieved],
                confidence=ConfidenceIndicator(score=0.65, rationale="Partial parse"),
                retrieved_chunks=len(retrieved),
            )

        return AgentOutput(
            agent=self.role,
            output=grounded.model_dump(),
            tokens_used=tokens,
            model=self.settings.openai_model,
            success=True,
        )

    def _mock_knowledge(self, query: str, retrieved: list[dict]) -> GroundedResponse:
        citations = [r["source"] for r in retrieved] or ["platform-knowledge-base"]
        return GroundedResponse(
            answer=(
                f"Based on enterprise knowledge base retrieval for '{query}': "
                "Multi-agent orchestration with shared memory enables reliable, "
                "governed AI workflows. Vector search provides semantic context enrichment "
                "while PostgreSQL stores workflow metadata and audit trails."
            ),
            citations=citations,
            confidence=ConfidenceIndicator(
                score=0.88,
                rationale=f"Retrieved {len(retrieved)} relevant chunks with high similarity",
                source_count=len(citations),
            ),
            retrieved_chunks=len(retrieved),
        )
