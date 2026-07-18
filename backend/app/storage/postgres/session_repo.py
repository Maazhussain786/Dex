"""PostgreSQL implementation of :class:`SessionRepository`."""

from __future__ import annotations

from datetime import UTC, datetime

import asyncpg

from app.domain.models import ExplorationSession
from app.storage.contracts import SessionRepository


class PgSessionRepository(SessionRepository):
    """Concrete session repository backed by asyncpg."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def save(self, session: ExplorationSession) -> None:
        """Insert a new session row."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO exploration_sessions (id, project_id, started_at, completed_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO NOTHING
                """,
                session.id,
                session.project_id,
                session.started_at,
                session.completed_at,
            )

    async def get(self, session_id: str) -> ExplorationSession | None:
        """Return a session by ID, or ``None``."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, project_id, started_at, completed_at FROM exploration_sessions WHERE id = $1",
                session_id,
            )
        if row is None:
            return None
        return _row_to_session(row)

    async def list_by_project(self, project_id: str) -> list[ExplorationSession]:
        """Return sessions for a project, newest first."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, project_id, started_at, completed_at
                FROM exploration_sessions
                WHERE project_id = $1
                ORDER BY started_at DESC
                """,
                project_id,
            )
        return [_row_to_session(row) for row in rows]

    async def mark_completed(self, session_id: str) -> None:
        """Set ``completed_at`` to the current UTC time."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE exploration_sessions SET completed_at = $1 WHERE id = $2",
                datetime.now(UTC),
                session_id,
            )


def _row_to_session(row: asyncpg.Record) -> ExplorationSession:
    """Map an asyncpg Record to a domain ExplorationSession."""
    return ExplorationSession(
        id=row["id"],
        project_id=row["project_id"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
    )
