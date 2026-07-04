from dataclasses import dataclass

from app.domain.models import Evidence


@dataclass(frozen=True)
class ExplorationTarget:
    project_id: str
    session_id: str
    url: str
    max_depth: int = 3


@dataclass(frozen=True)
class ExplorationReport:
    target: ExplorationTarget
    evidence: tuple[Evidence, ...]
    discovered_routes: tuple[str, ...]
    errors: tuple[str, ...] = ()


class BrowserExplorer:
    async def explore(self, target: ExplorationTarget) -> ExplorationReport:
        raise NotImplementedError
