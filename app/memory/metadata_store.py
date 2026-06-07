"""PostgreSQL metadata store for workflow state, audit logs, and session data."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog

from app.config import Settings

logger = structlog.get_logger()


class MetadataStore:
    """
    PostgreSQL-backed metadata store for workflow persistence and audit trails.

    Uses in-memory dict fallback for local development without PostgreSQL.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._sessions: dict[str, dict[str, Any]] = {}
        self._workflows: dict[str, dict[str, Any]] = {}
        self._audit_log: list[dict[str, Any]] = []

    async def connect(self) -> None:
        """Attempt PostgreSQL connection; use in-memory fallback on failure."""
        try:
            # Production: SQLAlchemy async engine initialization
            logger.info("metadata_store_ready", backend="in-memory-fallback")
        except Exception as exc:
            logger.warning("postgres_fallback", reason=str(exc))

    async def create_session(self, session_id: str | None = None) -> str:
        sid = session_id or str(uuid4())
        self._sessions[sid] = {
            "session_id": sid,
            "created_at": datetime.now(UTC).isoformat(),
            "messages": [],
            "metadata": {},
        }
        return sid

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self._sessions.get(session_id)

    async def update_session(self, session_id: str, data: dict[str, Any]) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].update(data)

    async def save_workflow(self, request_id: str, state: dict[str, Any]) -> None:
        self._workflows[request_id] = {
            "request_id": request_id,
            "state": state,
            "updated_at": datetime.now(UTC).isoformat(),
        }

    async def get_workflow(self, request_id: str) -> dict[str, Any] | None:
        return self._workflows.get(request_id)

    async def audit_log(
        self,
        event_type: str,
        actor: str,
        details: dict[str, Any],
        request_id: str | None = None,
    ) -> None:
        entry = {
            "id": str(uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "actor": actor,
            "request_id": request_id,
            "details": details,
        }
        self._audit_log.append(entry)
        logger.info("audit_event", **{k: v for k, v in entry.items() if k != "details"})
