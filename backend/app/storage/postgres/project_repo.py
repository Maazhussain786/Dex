"""PostgreSQL implementation of :class:`ProjectRepository`."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import asyncpg

from app.domain.models import Project, ProjectStatus
from app.storage.contracts import ProjectRepository


class PgProjectRepository(ProjectRepository):
    """Concrete project repository backed by asyncpg."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def save(self, project: Project) -> None:
        """Insert or update a project row."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO projects (id, name, target_url, description, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO UPDATE SET
                    name        = EXCLUDED.name,
                    target_url  = EXCLUDED.target_url,
                    description = EXCLUDED.description,
                    status      = EXCLUDED.status
                """,
                project.id,
                project.name,
                project.target_url,
                project.description,
                str(project.status),
                project.created_at,
            )

    async def get(self, project_id: str) -> Project | None:
        """Return a project by ID, or ``None``."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, target_url, description, status, created_at FROM projects WHERE id = $1",
                project_id,
            )
        if row is None:
            return None
        return _row_to_project(row)

    async def list_all(self) -> list[Project]:
        """Return all projects ordered by creation date descending."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name, target_url, description, status, created_at FROM projects ORDER BY created_at DESC"
            )
        return [_row_to_project(row) for row in rows]

    async def update_status(self, project_id: str, status: ProjectStatus) -> None:
        """Change project status."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE projects SET status = $1 WHERE id = $2",
                str(status),
                project_id,
            )


def _row_to_project(row: asyncpg.Record) -> Project:
    """Map an asyncpg Record to a domain Project."""
    return Project(
        id=row["id"],
        name=row["name"],
        target_url=row["target_url"],
        description=row["description"],
        status=ProjectStatus(row["status"]),
        created_at=row["created_at"],
    )
