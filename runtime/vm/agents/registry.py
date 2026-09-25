from __future__ import annotations

from dataclasses import dataclass, field

from .agent import AgentInstance


@dataclass
class AgentRegistry:
    """Registry for active CARDINAL agent instances."""

    agents: list[AgentInstance] = field(
        default_factory=list
    )

    def add(
        self,
        instance: AgentInstance,
    ) -> None:
        self.agents.append(instance)

    def remove(
        self,
        instance: AgentInstance,
    ) -> None:
        self.agents = [
            agent
            for agent in self.agents
            if agent is not instance
        ]

    def get(
        self,
        name: str,
    ) -> AgentInstance | None:
        for agent in self.agents:
            if agent.name == name:
                return agent

        return None

    def __iter__(self):
        return iter(self.agents)

    def __len__(self) -> int:
        return len(self.agents)
