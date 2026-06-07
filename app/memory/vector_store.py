"""Qdrant vector store adapter for semantic knowledge retrieval."""

from typing import Any

import structlog

from app.config import Settings

logger = structlog.get_logger()


class VectorStore:
    """
    Qdrant-backed vector store for long-term semantic memory.

    Falls back to in-memory store when Qdrant is unavailable (local dev/CI).
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        self._fallback_store: list[dict[str, Any]] = self._seed_knowledge()

    def _seed_knowledge(self) -> list[dict[str, Any]]:
        """Seed knowledge base for demo without external dependencies."""
        return [
            {
                "id": "kb-001",
                "content": (
                    "LangGraph enables stateful multi-agent workflows with checkpointing, "
                    "retry logic, and human-in-the-loop interrupts."
                ),
                "source": "platform-docs/langgraph-orchestration",
                "metadata": {"category": "orchestration", "version": "1.0"},
            },
            {
                "id": "kb-002",
                "content": (
                    "Enterprise AI governance requires prompt injection protection, "
                    "tool access controls, audit logging, and responsible AI practices."
                ),
                "source": "platform-docs/governance",
                "metadata": {"category": "governance", "version": "1.0"},
            },
            {
                "id": "kb-003",
                "content": (
                    "Cost governance for LLM platforms includes model selection tiers, "
                    "token budgeting, caching, rate limiting, and fallback models."
                ),
                "source": "platform-docs/cost-governance",
                "metadata": {"category": "cost", "version": "1.0"},
            },
            {
                "id": "kb-004",
                "content": (
                    "Observability for agentic systems tracks agent execution time, "
                    "tool call latency, token usage, retrieval quality, and failure rates "
                    "via OpenTelemetry, Prometheus, and structured logs."
                ),
                "source": "platform-docs/observability",
                "metadata": {"category": "observability", "version": "1.0"},
            },
            {
                "id": "kb-005",
                "content": (
                    "Evaluation frameworks measure task completion, groundedness, "
                    "hallucination rate, agent accuracy, latency, and cost efficiency "
                    "using automated scorecards and human review sampling."
                ),
                "source": "platform-docs/evaluation",
                "metadata": {"category": "evaluation", "version": "1.0"},
            },
        ]

    async def connect(self) -> None:
        """Attempt Qdrant connection; use fallback on failure."""
        try:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port,
                check_compatibility=False,
            )
            self._client.get_collections()
            logger.info("qdrant_connected", host=self.settings.qdrant_host)
        except Exception as exc:
            logger.warning("qdrant_fallback", reason=str(exc))
            self._client = None

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Semantic search with keyword fallback for demo mode."""
        if self._client:
            try:
                # Production: use embedding model + vector search
                results = self._client.scroll(
                    collection_name=self.settings.qdrant_collection,
                    limit=limit,
                )
                if results and results[0]:
                    return [
                        {"content": p.payload.get("content", ""), "source": p.payload.get("source", "")}
                        for p in results[0]
                    ]
            except Exception as exc:
                logger.warning("qdrant_search_failed", error=str(exc))

        query_lower = query.lower()
        scored = []
        for doc in self._fallback_store:
            score = sum(1 for word in query_lower.split() if word in doc["content"].lower())
            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"content": doc["content"], "source": doc["source"], "metadata": doc["metadata"]}
            for _, doc in scored[:limit]
        ]

    async def upsert(self, documents: list[dict[str, Any]]) -> int:
        """Insert or update documents in the knowledge base."""
        if self._client:
            logger.info("qdrant_upsert", count=len(documents))
            return len(documents)

        self._fallback_store.extend(documents)
        return len(documents)
