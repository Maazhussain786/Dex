from app.agents.base import Agent
from app.domain.models import AgentRole


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[AgentRole, Agent] = {}

    def register(self, agent: Agent) -> None:
        self._agents[agent.role] = agent

    def get(self, role: AgentRole) -> Agent:
        return self._agents[role]

    def roles(self) -> tuple[AgentRole, ...]:
        return tuple(self._agents)
