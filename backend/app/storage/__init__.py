"""Storage contracts — abstract repository interfaces.

All concrete adapters (PostgreSQL, Neo4j, Qdrant) implement these ABCs.
Application code programs exclusively against these interfaces so the
storage backend can be swapped or faked in tests without changing business
logic.
"""

from app.storage.contracts import (
    EvidenceRepository,
    GraphRepository,
    ProjectRepository,
    SessionRepository,
    VectorRepository,
)

__all__ = [
    "EvidenceRepository",
    "GraphRepository",
    "ProjectRepository",
    "SessionRepository",
    "VectorRepository",
]
