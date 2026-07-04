from app.agents.base import AgentResult, AgentTask
from app.agents.registry import AgentRegistry
from app.domain.models import AgentRole


class Coordinator:
    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    async def run_exploration_plan(self, task: AgentTask) -> tuple[AgentResult, ...]:
        planned_roles = (
            AgentRole.UI,
            AgentRole.NAVIGATION,
            AgentRole.NETWORK,
            AgentRole.FRAMEWORK,
            AgentRole.ARCHITECTURE,
        )

        results: list[AgentResult] = []
        for role in planned_roles:
            if role not in self._registry.roles():
                continue
            results.append(await self._registry.get(role).run(task))
        return tuple(results)
