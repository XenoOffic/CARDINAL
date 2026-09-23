from __future__ import annotations

from dataclasses import dataclass, field

from .messaging import AgentMessage


@dataclass
class SchedulerStats:
    """Runtime scheduler statistics."""

    ticks: int = 0
    events_processed: int = 0
    messages_processed: int = 0
    agents_scheduled: int = 0


@dataclass
class Scheduler:
    """
    Deterministic cooperative scheduler for CARDINAL agents.

    The scheduler never creates threads by itself. It processes
    agents in registration order, one unit of work at a time.
    """

    quantum: int = 1

    queue: list[str] = field(
        default_factory=list
    )

    stats: SchedulerStats = field(
        default_factory=SchedulerStats
    )

    def register(
        self,
        agent_name: str,
    ) -> None:
        if agent_name not in self.queue:
            self.queue.append(
                agent_name
            )

    def unregister(
        self,
        agent_name: str,
    ) -> None:
        self.queue = [
            name
            for name in self.queue
            if name != agent_name
        ]

    def clear(self) -> None:
        self.queue.clear()
        self.stats = SchedulerStats()

    def next_agent(self) -> str | None:
        if not self.queue:
            return None

        agent_name = self.queue.pop(0)

        self.queue.append(
            agent_name
        )

        return agent_name

    def tick(self) -> None:
        self.stats.ticks += 1
