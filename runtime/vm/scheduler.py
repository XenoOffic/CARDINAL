from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


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

    A work predicate may be supplied by the VM so the scheduler
    can distinguish registered agents that are idle from agents
    that have pending events or messages.
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

    def next_agent(
        self,
        has_work: Callable[[str], bool] | None = None,
    ) -> str | None:
        """
        Return the next scheduled agent.

        When ``has_work`` is provided, idle agents are skipped.
        The original registration order remains deterministic.
        """

        if not self.queue:
            return None

        if has_work is None:
            agent_name = self.queue.pop(0)

            self.queue.append(
                agent_name
            )

            return agent_name

        queue_length = len(self.queue)

        for _ in range(queue_length):
            agent_name = self.queue.pop(0)

            self.queue.append(
                agent_name
            )

            if has_work(agent_name):
                return agent_name

        return None

    def tick(self) -> None:
        self.stats.ticks += 1
