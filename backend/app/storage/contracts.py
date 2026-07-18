"""Abstract repository interfaces for the Dex storage layer.

Each interface defines the minimal contract that a concrete adapter must
fulfil.  Domain objects flow in and out — no ORM models leak beyond this
boundary.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.models import (
    Evidence,
    ExplorationSession,
    GraphEdge,
    GraphNode,
    Project,
    ProjectStatus,
)


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class ProjectRepository(ABC):
    """Persist and retrieve :class:`Project` aggregates."""

    @abstractmethod
    async def save(self, project: Project) -> None:
        """Insert or update a project."""

    @abstractmethod
    async def get(self, project_id: str) -> Project | None:
        """Return a project by ID, or ``None`` if not found."""

    @abstractmethod
    async def list_all(self) -> list[Project]:
        """Return every project, ordered by creation date descending."""

    @abstractmethod
    async def update_status(self, project_id: str, status: ProjectStatus) -> None:
        """Change the status of an existing project."""


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class SessionRepository(ABC):
    """Persist and retrieve :class:`ExplorationSession` records."""

    @abstractmethod
    async def save(self, session: ExplorationSession) -> None:
        """Insert a new session."""

    @abstractmethod
    async def get(self, session_id: str) -> ExplorationSession | None:
        """Return a session by ID, or ``None`` if not found."""

    @abstractmethod
    async def list_by_project(self, project_id: str) -> list[ExplorationSession]:
        """Return all sessions for a project, ordered by start time descending."""

    @abstractmethod
    async def mark_completed(self, session_id: str) -> None:
        """Set ``completed_at`` to the current UTC time."""


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class EvidenceRepository(ABC):
    """Persist and retrieve :class:`Evidence` items."""

    @abstractmethod
    async def save_many(self, items: list[Evidence]) -> None:
        """Bulk-insert a batch of evidence items."""

    @abstractmethod
    async def get(self, evidence_id: str) -> Evidence | None:
        """Return a single evidence item by ID."""

    @abstractmethod
    async def list_by_session(
        self,
        session_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Evidence]:
        """Return paginated evidence for a session, newest first."""


# ---------------------------------------------------------------------------
# Knowledge Graph
# ---------------------------------------------------------------------------

class GraphRepository(ABC):
    """Persist and query the knowledge graph (nodes + edges)."""

    @abstractmethod
    async def save_node(self, node: GraphNode) -> None:
        """Create or merge a graph node."""

    @abstractmethod
    async def save_edge(self, edge: GraphEdge) -> None:
        """Create or merge a graph edge."""

    @abstractmethod
    async def get_node(self, node_id: str) -> GraphNode | None:
        """Return a node by ID."""

    @abstractmethod
    async def get_neighbours(
        self,
        node_id: str,
        *,
        relationship: str | None = None,
        direction: str = "both",
    ) -> list[GraphNode]:
        """Return nodes connected to *node_id*, optionally filtered by relationship type."""

    @abstractmethod
    async def query(self, cypher: str, parameters: dict[str, object] | None = None) -> list[dict[str, object]]:
        """Execute a raw Cypher query and return result rows as dicts."""


# ---------------------------------------------------------------------------
# Vector Search
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VectorSearchResult:
    """A single result from a similarity search."""

    id: str
    score: float
    payload: dict[str, object]


class VectorRepository(ABC):
    """Store and search vector embeddings."""

    @abstractmethod
    async def upsert(
        self,
        collection: str,
        id: str,
        vector: list[float],
        payload: dict[str, object],
    ) -> None:
        """Insert or update a vector point."""

    @abstractmethod
    async def search(
        self,
        collection: str,
        vector: list[float],
        *,
        limit: int = 10,
        score_threshold: float = 0.0,
    ) -> list[VectorSearchResult]:
        """Return the nearest neighbours above the score threshold."""
