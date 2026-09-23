from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .observability import RuntimeEvent, RuntimeHistory


@dataclass
class BehaviorStatistics:
    """Aggregated statistics for one behavior."""

    behavior: str
    started: int = 0
    completed: int = 0
    errors: int = 0

    @property
    def success_rate(self) -> float:
        total = self.completed + self.errors

        if total == 0:
            return 0.0

        return self.completed / total


@dataclass
class AgentStatistics:
    """Aggregated runtime statistics for one agent."""

    agent: str
    events: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    behaviors_started: int = 0
    behaviors_completed: int = 0
    errors: int = 0


@dataclass
class RuntimeSnapshot:
    """Point-in-time summary of runtime activity."""

    total_events: int
    agents: dict[str, AgentStatistics] = field(
        default_factory=dict
    )
    behaviors: dict[str, BehaviorStatistics] = field(
        default_factory=dict
    )
    error_events: list[RuntimeEvent] = field(
        default_factory=list
    )


class RuntimeIntelligence:
    """
    Analysis layer built on top of RuntimeHistory.

    This component does not modify runtime state.
    It observes history and produces deterministic
    statistics and snapshots.
    """

    def __init__(
        self,
        history: RuntimeHistory,
    ) -> None:
        self.history = history

    def snapshot(self) -> RuntimeSnapshot:
        """Build a complete runtime snapshot."""

        agents: dict[str, AgentStatistics] = {}
        behaviors: dict[str, BehaviorStatistics] = {}
        errors: list[RuntimeEvent] = []

        for event in self.history.events:
            self._process_event(
                event,
                agents,
                behaviors,
                errors,
            )

        return RuntimeSnapshot(
            total_events=len(
                self.history.events
            ),
            agents=agents,
            behaviors=behaviors,
            error_events=errors,
        )

    def agent_statistics(
        self,
        agent_name: str,
    ) -> AgentStatistics:
        """Return statistics for one agent."""

        snapshot = self.snapshot()

        return snapshot.agents.get(
            agent_name,
            AgentStatistics(
                agent=agent_name
            ),
        )

    def behavior_statistics(
        self,
        behavior_name: str,
    ) -> BehaviorStatistics:
        """Return statistics for one behavior."""

        snapshot = self.snapshot()

        return snapshot.behaviors.get(
            behavior_name,
            BehaviorStatistics(
                behavior=behavior_name
            ),
        )

    def recent_errors(
        self,
        limit: int = 10,
    ) -> list[RuntimeEvent]:
        """Return the most recent runtime errors."""

        if limit < 0:
            raise ValueError(
                "limit cannot be negative."
            )

        errors = [
            event
            for event in self.history.events
            if event.event_type
            == "runtime.error"
        ]

        if limit == 0:
            return []

        return errors[-limit:]

    def detect_patterns(
        self,
    ) -> list[dict[str, Any]]:
        """
        Detect simple deterministic runtime patterns.

        These are observations, not autonomous decisions.
        """

        snapshot = self.snapshot()
        patterns: list[dict[str, Any]] = []

        for agent in snapshot.agents.values():
            if agent.errors > 0:
                patterns.append(
                    {
                        "type": "agent.errors",
                        "agent": agent.agent,
                        "count": agent.errors,
                    }
                )

        for behavior in snapshot.behaviors.values():
            if behavior.errors > 0:
                patterns.append(
                    {
                        "type": "behavior.errors",
                        "behavior": behavior.behavior,
                        "count": behavior.errors,
                    }
                )

            if (
                behavior.completed > 0
                and behavior.success_rate < 1.0
            ):
                patterns.append(
                    {
                        "type": "behavior.instability",
                        "behavior": behavior.behavior,
                        "success_rate": (
                            behavior.success_rate
                        ),
                    }
                )

        return patterns

    @staticmethod
    def _process_event(
        event: RuntimeEvent,
        agents: dict[str, AgentStatistics],
        behaviors: dict[str, BehaviorStatistics],
        errors: list[RuntimeEvent],
    ) -> None:
        if event.agent is not None:
            agent = agents.setdefault(
                event.agent,
                AgentStatistics(
                    agent=event.agent
                ),
            )

            if event.event_type in {
                "agent.spawned",
                "agent.started",
                "agent.stopped",
                "event.processed",
            }:
                agent.events += 1

            elif event.event_type == "message.sent":
                agent.messages_sent += 1

            elif event.event_type == "message.received":
                agent.messages_received += 1

            elif event.event_type == "behavior.started":
                agent.behaviors_started += 1

            elif event.event_type == "behavior.completed":
                agent.behaviors_completed += 1

            elif event.event_type == "runtime.error":
                agent.errors += 1

        if event.behavior is not None:
            behavior = behaviors.setdefault(
                event.behavior,
                BehaviorStatistics(
                    behavior=event.behavior
                ),
            )

            if event.event_type == "behavior.started":
                behavior.started += 1

            elif event.event_type == "behavior.completed":
                behavior.completed += 1

            elif event.event_type == "runtime.error":
                behavior.errors += 1

        if event.event_type == "runtime.error":
            errors.append(event)
