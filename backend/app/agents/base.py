from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.models import AgentRole, Evidence


@dataclass(frozen=True)
class AgentTask:
    project_id: str
    session_id: str
    goal: str
    context: dict[str, object]


@dataclass(frozen=True)
class AgentResult:
    role: AgentRole
    summary: str
    evidence: tuple[Evidence, ...] = ()
    findings: tuple[str, ...] = ()


class Agent(ABC):
    role: AgentRole

    @abstractmethod
    async def run(self, task: AgentTask) -> AgentResult:
        """Execute an agent task and return structured findings."""
