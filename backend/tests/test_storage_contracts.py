"""Unit tests for storage contracts using in-memory fakes.

These tests verify the contract semantics — save/get round-trip, listing,
pagination, status updates — without any database dependency.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.models import (
    Evidence,
    EvidenceType,
    ExplorationSession,
    GraphEdge,
    GraphNode,
    Project,
    ProjectStatus,
)
from app.storage.contracts import (
    EvidenceRepository,
    GraphRepository,
    ProjectRepository,
    SessionRepository,
    VectorRepository,
    VectorSearchResult,
)


# ===================================================================
# In-memory fakes
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
        # Reconstruct with new status (frozen dataclass).
        self._store[project_id] = Project(
            id=old.id,
            name=old.name,
            target_url=old.target_url,
            description=old.description,
            status=status,
            created_at=old.created_at,
        )


class FakeSessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._store: dict[str, ExplorationSession] = {}

    async def save(self, session: ExplorationSession) -> None:
        self._store[session.id] = session

    async def get(self, session_id: str) -> ExplorationSession | None:
        return self._store.get(session_id)

    async def list_by_project(self, project_id: str) -> list[ExplorationSession]:
        return sorted(
            [s for s in self._store.values() if s.project_id == project_id],
            key=lambda s: s.started_at,
            reverse=True,
        )

    async def mark_completed(self, session_id: str) -> None:
        old = self._store.get(session_id)
        if old is None:
            return
        self._store[session_id] = ExplorationSession(
            id=old.id,
            project_id=old.project_id,
            started_at=old.started_at,
            completed_at=datetime.now(UTC),
        )


class FakeEvidenceRepository(EvidenceRepository):
    def __init__(self) -> None:
        self._store: list[Evidence] = []

    async def save_many(self, items: list[Evidence]) -> None:
        existing_ids = {e.id for e in self._store}
        for item in items:
            if item.id not in existing_ids:
                self._store.append(item)
                existing_ids.add(item.id)

    async def get(self, evidence_id: str) -> Evidence | None:
        for item in self._store:
            if item.id == evidence_id:
                return item
        return None

    async def list_by_session(
        self,
        session_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Evidence]:
        filtered = sorted(
            [e for e in self._store if e.session_id == session_id],
            key=lambda e: e.collected_at,
            reverse=True,
        )
        return filtered[offset : offset + limit]


class FakeGraphRepository(GraphRepository):
    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []

    async def save_node(self, node: GraphNode) -> None:
        self._nodes[node.id] = node

    async def save_edge(self, edge: GraphEdge) -> None:
        self._edges.append(edge)

    async def get_node(self, node_id: str) -> GraphNode | None:
        return self._nodes.get(node_id)

    async def get_neighbours(
        self,
        node_id: str,
        *,
        relationship: str | None = None,
        direction: str = "both",
    ) -> list[GraphNode]:
        neighbours: list[GraphNode] = []
        for edge in self._edges:
            if direction in ("out", "both") and edge.source_id == node_id:
                if relationship is None or edge.relationship == relationship:
                    node = self._nodes.get(edge.target_id)
                    if node:
                        neighbours.append(node)
            if direction in ("in", "both") and edge.target_id == node_id:
                if relationship is None or edge.relationship == relationship:
                    node = self._nodes.get(edge.source_id)
                    if node:
                        neighbours.append(node)
        return neighbours

    async def query(self, cypher: str, parameters: dict[str, object] | None = None) -> list[dict[str, object]]:
        return []  # Fake does not support Cypher


class FakeVectorRepository(VectorRepository):
    def __init__(self) -> None:
        self._points: dict[str, dict[str, object]] = {}

    async def upsert(
        self,
        collection: str,
        id: str,
        vector: list[float],
        payload: dict[str, object],
    ) -> None:
        self._points[f"{collection}:{id}"] = {"vector": vector, "payload": payload}

    async def search(
        self,
        collection: str,
        vector: list[float],
        *,
        limit: int = 10,
        score_threshold: float = 0.0,
    ) -> list[VectorSearchResult]:
        # Return all stored points in the collection (no actual similarity).
        results = []
        prefix = f"{collection}:"
        for key, data in self._points.items():
            if key.startswith(prefix):
                point_id = key[len(prefix) :]
                results.append(VectorSearchResult(id=point_id, score=1.0, payload=data["payload"]))
        return results[:limit]


# ===================================================================
# Tests
# ===================================================================


class TestProjectRepository:
    @pytest.fixture
    def repo(self) -> FakeProjectRepository:
        return FakeProjectRepository()

    async def test_save_and_get(self, repo: FakeProjectRepository) -> None:
        project = Project.create(name="Test", target_url="https://example.com")
        await repo.save(project)
        result = await repo.get(project.id)
        assert result is not None
        assert result.id == project.id
        assert result.name == "Test"

    async def test_get_nonexistent_returns_none(self, repo: FakeProjectRepository) -> None:
        result = await repo.get("nonexistent")
        assert result is None

    async def test_list_all(self, repo: FakeProjectRepository) -> None:
        p1 = Project.create(name="A", target_url="https://a.com")
        p2 = Project.create(name="B", target_url="https://b.com")
        await repo.save(p1)
        await repo.save(p2)
        all_projects = await repo.list_all()
        assert len(all_projects) == 2

    async def test_update_status(self, repo: FakeProjectRepository) -> None:
        project = Project.create(name="Test", target_url="https://example.com")
        await repo.save(project)
        await repo.update_status(project.id, ProjectStatus.EXPLORING)
        updated = await repo.get(project.id)
        assert updated is not None
        assert updated.status == ProjectStatus.EXPLORING


class TestSessionRepository:
    @pytest.fixture
    def repo(self) -> FakeSessionRepository:
        return FakeSessionRepository()

    async def test_save_and_get(self, repo: FakeSessionRepository) -> None:
        session = ExplorationSession.start("proj-1")
        await repo.save(session)
        result = await repo.get(session.id)
        assert result is not None
        assert result.project_id == "proj-1"

    async def test_list_by_project(self, repo: FakeSessionRepository) -> None:
        s1 = ExplorationSession.start("proj-1")
        s2 = ExplorationSession.start("proj-1")
        s3 = ExplorationSession.start("proj-2")
        await repo.save(s1)
        await repo.save(s2)
        await repo.save(s3)
        sessions = await repo.list_by_project("proj-1")
        assert len(sessions) == 2

    async def test_mark_completed(self, repo: FakeSessionRepository) -> None:
        session = ExplorationSession.start("proj-1")
        await repo.save(session)
        assert session.completed_at is None
        await repo.mark_completed(session.id)
        updated = await repo.get(session.id)
        assert updated is not None
        assert updated.completed_at is not None


class TestEvidenceRepository:
    @pytest.fixture
    def repo(self) -> FakeEvidenceRepository:
        return FakeEvidenceRepository()

    async def test_save_many_and_get(self, repo: FakeEvidenceRepository) -> None:
        e1 = Evidence.collect("p1", "s1", EvidenceType.DOM_SNAPSHOT, "Page A")
        e2 = Evidence.collect("p1", "s1", EvidenceType.SCREENSHOT, "Screenshot A")
        await repo.save_many([e1, e2])
        result = await repo.get(e1.id)
        assert result is not None
        assert result.summary == "Page A"

    async def test_list_by_session(self, repo: FakeEvidenceRepository) -> None:
        items = [
            Evidence.collect("p1", "s1", EvidenceType.DOM_SNAPSHOT, f"Item {i}")
            for i in range(5)
        ]
        await repo.save_many(items)
        result = await repo.list_by_session("s1", limit=3, offset=0)
        assert len(result) == 3

    async def test_pagination_offset(self, repo: FakeEvidenceRepository) -> None:
        items = [
            Evidence.collect("p1", "s1", EvidenceType.CONSOLE_LOG, f"Item {i}")
            for i in range(5)
        ]
        await repo.save_many(items)
        page2 = await repo.list_by_session("s1", limit=3, offset=3)
        assert len(page2) == 2

    async def test_duplicate_items_ignored(self, repo: FakeEvidenceRepository) -> None:
        e1 = Evidence.collect("p1", "s1", EvidenceType.DOM_SNAPSHOT, "Page A")
        await repo.save_many([e1])
        await repo.save_many([e1])  # duplicate
        all_items = await repo.list_by_session("s1")
        assert len(all_items) == 1


class TestGraphRepository:
    @pytest.fixture
    def repo(self) -> FakeGraphRepository:
        return FakeGraphRepository()

    async def test_save_and_get_node(self, repo: FakeGraphRepository) -> None:
        node = GraphNode(id="n1", label="Login Page", kind="Page")
        await repo.save_node(node)
        result = await repo.get_node("n1")
        assert result is not None
        assert result.label == "Login Page"

    async def test_get_neighbours(self, repo: FakeGraphRepository) -> None:
        n1 = GraphNode(id="n1", label="Page A", kind="Page")
        n2 = GraphNode(id="n2", label="API /login", kind="APIEndpoint")
        edge = GraphEdge(source_id="n1", target_id="n2", relationship="SUBMITS")
        await repo.save_node(n1)
        await repo.save_node(n2)
        await repo.save_edge(edge)
        neighbours = await repo.get_neighbours("n1", direction="out")
        assert len(neighbours) == 1
        assert neighbours[0].id == "n2"

    async def test_get_neighbours_filtered_by_relationship(self, repo: FakeGraphRepository) -> None:
        n1 = GraphNode(id="n1", label="Page", kind="Page")
        n2 = GraphNode(id="n2", label="Button", kind="Component")
        n3 = GraphNode(id="n3", label="API", kind="APIEndpoint")
        await repo.save_node(n1)
        await repo.save_node(n2)
        await repo.save_node(n3)
        await repo.save_edge(GraphEdge(source_id="n1", target_id="n2", relationship="CONTAINS"))
        await repo.save_edge(GraphEdge(source_id="n1", target_id="n3", relationship="SUBMITS"))
        contains = await repo.get_neighbours("n1", relationship="CONTAINS", direction="out")
        assert len(contains) == 1
        assert contains[0].id == "n2"


class TestVectorRepository:
    @pytest.fixture
    def repo(self) -> FakeVectorRepository:
        return FakeVectorRepository()

    async def test_upsert_and_search(self, repo: FakeVectorRepository) -> None:
        await repo.upsert("evidence", "v1", [0.1, 0.2, 0.3], {"summary": "login page"})
        results = await repo.search("evidence", [0.1, 0.2, 0.3], limit=5)
        assert len(results) == 1
        assert results[0].id == "v1"
        assert results[0].payload["summary"] == "login page"

    async def test_search_limit(self, repo: FakeVectorRepository) -> None:
        for i in range(5):
            await repo.upsert("coll", f"v{i}", [float(i)], {"i": i})
        results = await repo.search("coll", [0.0], limit=2)
        assert len(results) == 2
