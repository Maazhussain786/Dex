"""PostgreSQL implementation of :class:`EvidenceRepository`."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import asyncpg

from app.domain.models import Evidence, EvidenceType
from app.storage.contracts import EvidenceRepository


class PgEvidenceRepository(EvidenceRepository):
    """Concrete evidence repository backed by asyncpg."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def save_many(self, items: list[Evidence]) -> None:
        """Bulk-insert evidence items.

        Uses a prepared statement in a transaction for best performance.
        """
        if not items:
            return

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                stmt = await conn.prepare(
                    """
                    INSERT INTO evidence (id, project_id, session_id, evidence_type, summary, payload, collected_at)
                    VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
                    ON CONFLICT (id) DO NOTHING
                    """
                )
                for item in items:
                    await stmt.fetch(
                        item.id,
                        item.project_id,
                        item.session_id,
                        str(item.evidence_type),
                        item.summary,
                        json.dumps(item.payload, default=str),
                        item.collected_at,
                    )

    async def get(self, evidence_id: str) -> Evidence | None:
        """Return a single evidence item by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, project_id, session_id, evidence_type, summary, payload, collected_at
                FROM evidence WHERE id = $1
                """,
                evidence_id,
            )
        if row is None:
            return None
        return _row_to_evidence(row)

    async def list_by_session(
        self,
        session_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Evidence]:
        """Return paginated evidence for a session, newest first."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, project_id, session_id, evidence_type, summary, payload, collected_at
                FROM evidence
                WHERE session_id = $1
                ORDER BY collected_at DESC
                LIMIT $2 OFFSET $3
                """,
                session_id,
                limit,
                offset,
            )
        return [_row_to_evidence(row) for row in rows]


def _row_to_evidence(row: asyncpg.Record) -> Evidence:
    """Map an asyncpg Record to a domain Evidence."""
    payload = row["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)

    return Evidence(
        id=row["id"],
        project_id=row["project_id"],
        session_id=row["session_id"],
        evidence_type=EvidenceType(row["evidence_type"]),
        summary=row["summary"],
        payload=payload,
        collected_at=row["collected_at"],
    )
