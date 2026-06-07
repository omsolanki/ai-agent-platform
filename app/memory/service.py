"""Unified memory service — short-term context + long-term knowledge."""

from typing import Any

import structlog

from app.config import Settings, get_settings
from app.memory.metadata_store import MetadataStore
from app.memory.vector_store import VectorStore

logger = structlog.get_logger()


class MemoryService:
    """
    Orchestrates short-term (conversation) and long-term (vector + metadata) memory.

    Short-term: In-process shared memory passed via LangGraph state
    Long-term: Qdrant (vectors) + PostgreSQL (metadata, audit, sessions)
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.vector_store = VectorStore(self.settings)
        self.metadata_store = MetadataStore(self.settings)
        self._initialized = False

    async def initialize(self) -> None:
        if not self._initialized:
            await self.vector_store.connect()
            await self.metadata_store.connect()
            self._initialized = True
            logger.info("memory_service_initialized")

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        await self.initialize()
        return await self.vector_store.search(query, limit=limit)

    async def get_or_create_session(self, session_id: str | None = None) -> str:
        await self.initialize()
        if session_id:
            existing = await self.metadata_store.get_session(session_id)
            if existing:
                return session_id
        return await self.metadata_store.create_session(session_id)

    async def update_conversation(
        self, session_id: str, role: str, content: str
    ) -> None:
        session = await self.metadata_store.get_session(session_id)
        if session:
            session["messages"].append(
                {"role": role, "content": content, "timestamp": __import__("datetime").datetime.utcnow().isoformat()}
            )
            await self.metadata_store.update_session(session_id, session)

    def build_shared_memory(self, session_id: str | None, context: dict[str, Any]) -> dict[str, Any]:
        """Build shared memory dict for agent context passing."""
        return {
            "session_id": session_id,
            "conversation_history": context.get("conversation_history", []),
            "user_context": context.get("user_context", {}),
            "agent_outputs": context.get("agent_outputs", []),
        }

    async def persist_workflow(self, request_id: str, state: dict[str, Any]) -> None:
        await self.metadata_store.save_workflow(request_id, state)
        await self.metadata_store.audit_log(
            event_type="workflow_completed",
            actor="orchestrator",
            details={"status": state.get("status", "unknown")},
            request_id=request_id,
        )

    async def audit(self, event_type: str, actor: str, details: dict[str, Any], request_id: str | None = None) -> None:
        await self.metadata_store.audit_log(event_type, actor, details, request_id)

    async def save_run_snapshot(self, snapshot: dict[str, Any]) -> None:
        await self.initialize()
        await self.metadata_store.save_run_snapshot(snapshot)

    async def list_run_history(self, limit: int = 10) -> list[dict[str, Any]]:
        await self.initialize()
        return await self.metadata_store.list_run_history(limit=limit)

    async def get_run_snapshot(self, request_id: str) -> dict[str, Any] | None:
        await self.initialize()
        return await self.metadata_store.get_run_snapshot(request_id)
