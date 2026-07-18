"""Tests for the session and evidence API endpoints.

Uses in-memory fake repositories so no database is required.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.domain.models import (
    Evidence,
    EvidenceType,
    ExplorationSession,
    Project,
    ProjectStatus,
)
from app.storage.contracts import EvidenceRepository, ProjectRepository, SessionRepository


# ===================================================================
# Fakes (same as test_storage_contracts but inlined for independence)
# ===================================================================

class FakeProjectRepository(ProjectRepository):
    def __init__(self) -> None:
        self._store: dict[str, Project] = {}

    async def save(self, project: Project) -> None:
        self._store[project.id] = project

    async def get(self, project_id: str) -> Project | None:
        return self._store.get(project_id)

    async def list_all(self) -> list[Project]:
        return sorted(self._store.values(), key=lambda p: p.created_at, reverse=True)

    async def update_status(self, project_id: str, status: ProjectStatus) -> None:
        old = self._store.get(project_id)
        if old is None:
            return
        self._store[project_id] = Project(
            id=old.id, name=old.name, target_url=old.target_url,
            description=old.description, status=status, created_at=old.created_at,
        )


class FakeSessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._store: dict[str, ExplorationSession] = {}

    async def save(self, session: ExplorationSession) -> None:
        self._store[session.id] = session

    async def get(self, session_id: str) -> ExplorationSession | None:
        return self._store.get(session_id)

    async def list_by_project(self, project_id: str) -> list[ExplorationSession]:
        return [s for s in self._store.values() if s.project_id == project_id]

    async def mark_completed(self, session_id: str) -> None:
        old = self._store.get(session_id)
        if old is None:
            return
        self._store[session_id] = ExplorationSession(
            id=old.id, project_id=old.project_id,
            started_at=old.started_at, completed_at=datetime.now(UTC),
        )


class FakeEvidenceRepository(EvidenceRepository):
    def __init__(self) -> None:
        self._store: list[Evidence] = []

    async def save_many(self, items: list[Evidence]) -> None:
        self._store.extend(items)

    async def get(self, evidence_id: str) -> Evidence | None:
        for item in self._store:
            if item.id == evidence_id:
                return item
        return None

    async def list_by_session(
        self, session_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[Evidence]:
        filtered = [e for e in self._store if e.session_id == session_id]
        return filtered[offset : offset + limit]


# ===================================================================
# Test app fixture
# ===================================================================

def _create_test_app() -> tuple[FastAPI, FakeProjectRepository, FakeSessionRepository, FakeEvidenceRepository]:
    """Build a minimal FastAPI app with fake repositories."""
    from app.api.routes.projects import router as projects_router
    from app.api.routes.sessions import router as sessions_router

    app = FastAPI()
    project_repo = FakeProjectRepository()
    session_repo = FakeSessionRepository()
    evidence_repo = FakeEvidenceRepository()

    app.state.project_repo = project_repo
    app.state.session_repo = session_repo
    app.state.evidence_repo = evidence_repo

    app.include_router(projects_router, prefix="/projects")
    app.include_router(sessions_router, prefix="/projects")

    return app, project_repo, session_repo, evidence_repo


# ===================================================================
# Tests
# ===================================================================


class TestProjectsAPI:
    def setup_method(self) -> None:
        self.app, self.project_repo, self.session_repo, self.evidence_repo = _create_test_app()
        self.client = TestClient(self.app)

    def test_create_project(self) -> None:
        resp = self.client.post("/projects", json={
            "name": "My App",
            "target_url": "https://example.com",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My App"
        assert data["status"] == "draft"

    def test_list_projects(self) -> None:
        self.client.post("/projects", json={"name": "A", "target_url": "https://a.com"})
        self.client.post("/projects", json={"name": "B", "target_url": "https://b.com"})
        resp = self.client.get("/projects")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_project_not_found(self) -> None:
        resp = self.client.get("/projects/nonexistent")
        assert resp.status_code == 404


class TestSessionsAPI:
    def setup_method(self) -> None:
        self.app, self.project_repo, self.session_repo, self.evidence_repo = _create_test_app()
        self.client = TestClient(self.app)

    def _create_project(self) -> str:
        resp = self.client.post("/projects", json={
            "name": "Test",
            "target_url": "https://example.com",
        })
        return resp.json()["id"]

    def test_create_session(self) -> None:
        project_id = self._create_project()
        resp = self.client.post(f"/projects/{project_id}/sessions", json={"max_depth": 1})
        assert resp.status_code == 201
        data = resp.json()
        assert data["project_id"] == project_id
        assert data["completed_at"] is None

    def test_create_session_project_not_found(self) -> None:
        resp = self.client.post("/projects/nonexistent/sessions", json={})
        assert resp.status_code == 404

    def test_get_session(self) -> None:
        project_id = self._create_project()
        create_resp = self.client.post(f"/projects/{project_id}/sessions", json={})
        session_id = create_resp.json()["id"]
        resp = self.client.get(f"/projects/{project_id}/sessions/{session_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == session_id

    def test_get_session_not_found(self) -> None:
        project_id = self._create_project()
        resp = self.client.get(f"/projects/{project_id}/sessions/nonexistent")
        assert resp.status_code == 404

    def test_list_evidence_empty(self) -> None:
        project_id = self._create_project()
        create_resp = self.client.post(f"/projects/{project_id}/sessions", json={})
        session_id = create_resp.json()["id"]
        resp = self.client.get(f"/projects/{project_id}/sessions/{session_id}/evidence")
        assert resp.status_code == 200
        assert resp.json() == []
