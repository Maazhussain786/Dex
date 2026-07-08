"""Contracts for the browser exploration pipeline.

These data classes define the inputs, outputs, and status tracking for
exploration runs.  Concrete implementations live in ``browser_explorer``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.domain.models import Evidence


class ExplorationStatus(StrEnum):
    """Lifecycle state of a single exploration run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class Credentials:
    """Optional login credentials for authenticated exploration."""

    username: str
    password: str
    login_url: str | None = None


@dataclass(frozen=True)
class ExplorationTarget:
    """Describes what to explore and how."""

    project_id: str
    session_id: str
    url: str
    max_depth: int = 3
    credentials: Credentials | None = None
    screenshot_enabled: bool = True
    network_capture_enabled: bool = True


@dataclass(frozen=True)
class ExplorationReport:
    """Result of a completed exploration run."""

    target: ExplorationTarget
    status: ExplorationStatus = ExplorationStatus.COMPLETED
    evidence: tuple[Evidence, ...] = ()
    discovered_routes: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    pages_visited: int = 0


@dataclass
class ExplorationProgress:
    """Mutable progress tracker shared with callers during a run."""

    status: ExplorationStatus = ExplorationStatus.PENDING
    pages_visited: int = 0
    evidence_collected: int = 0
    current_url: str = ""
    errors: list[str] = field(default_factory=list)


class BrowserExplorer:
    """Abstract interface for browser-based exploration.

    Concrete implementations should override ``explore``.
    """

    async def explore(self, target: ExplorationTarget) -> ExplorationReport:
        raise NotImplementedError
