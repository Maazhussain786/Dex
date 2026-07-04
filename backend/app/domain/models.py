from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    EXPLORING = "exploring"
    ANALYZING = "analyzing"
    READY = "ready"
    FAILED = "failed"


class EvidenceType(StrEnum):
    DOM_SNAPSHOT = "dom_snapshot"
    SCREENSHOT = "screenshot"
    NETWORK_REQUEST = "network_request"
    CONSOLE_LOG = "console_log"
    NAVIGATION_EVENT = "navigation_event"
    SOURCE_FILE = "source_file"
    ANALYSIS_FINDING = "analysis_finding"


class AgentRole(StrEnum):
    COORDINATOR = "coordinator"
    UI = "ui"
    NAVIGATION = "navigation"
    NETWORK = "network"
    FRAMEWORK = "framework"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    REASONING = "reasoning"


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    target_url: str
    description: str | None
    status: ProjectStatus
    created_at: datetime

    @classmethod
    def create(cls, name: str, target_url: str, description: str | None = None) -> "Project":
        return cls(
            id=str(uuid4()),
            name=name,
            target_url=target_url,
            description=description,
            status=ProjectStatus.DRAFT,
            created_at=datetime.now(UTC),
        )


@dataclass(frozen=True)
class ExplorationSession:
    id: str
    project_id: str
    started_at: datetime
    completed_at: datetime | None = None

    @classmethod
    def start(cls, project_id: str) -> "ExplorationSession":
        return cls(id=str(uuid4()), project_id=project_id, started_at=datetime.now(UTC))


@dataclass(frozen=True)
class Evidence:
    id: str
    project_id: str
    session_id: str
    evidence_type: EvidenceType
    summary: str
    payload: dict[str, object] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def collect(
        cls,
        project_id: str,
        session_id: str,
        evidence_type: EvidenceType,
        summary: str,
        payload: dict[str, object] | None = None,
    ) -> "Evidence":
        return cls(
            id=str(uuid4()),
            project_id=project_id,
            session_id=session_id,
            evidence_type=evidence_type,
            summary=summary,
            payload=payload or {},
        )


@dataclass(frozen=True)
class GraphNode:
    id: str
    label: str
    kind: str
    properties: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    relationship: str
    evidence_ids: tuple[str, ...] = ()
