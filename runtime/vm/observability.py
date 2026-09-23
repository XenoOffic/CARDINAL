from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass(frozen=True)
class RuntimeEvent:
    """Structured event emitted by the CARDINAL runtime."""

    event_type: str
    timestamp: float
    agent: str | None = None
    behavior: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class RuntimeHistory:
    """
    Bounded structured history for CARDINAL runtime activity.

    History is intentionally bounded so observability cannot
    consume unlimited memory during long-running execution.
    """

    def __init__(
        self,
        max_events: int = 1000,
    ) -> None:
        if max_events < 1:
            raise ValueError(
                "max_events must be greater than zero."
            )

        self.max_events = max_events
        self._events: list[RuntimeEvent] = []

    @property
    def events(self) -> list[RuntimeEvent]:
        """Return a copy of the recorded history."""
        return list(self._events)

    def record(
        self,
        event_type: str,
        *,
        agent: str | None = None,
        behavior: str | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeEvent:
        if not event_type:
            raise ValueError(
                "event_type cannot be empty."
            )

        event = RuntimeEvent(
            event_type=event_type,
            timestamp=time(),
            agent=agent,
            behavior=behavior,
            source=source,
            metadata=dict(
                metadata or {}
            ),
        )

        self._events.append(event)

        if len(self._events) > self.max_events:
            del self._events[
                :len(self._events) - self.max_events
            ]

        return event

    def clear(self) -> None:
        self._events.clear()

    def filter(
        self,
        event_type: str | None = None,
        agent: str | None = None,
    ) -> list[RuntimeEvent]:
        events = self._events

        if event_type is not None:
            events = [
                event
                for event in events
                if event.event_type == event_type
            ]

        if agent is not None:
            events = [
                event
                for event in events
                if event.agent == agent
            ]

        return list(events)

    def count(
        self,
        event_type: str | None = None,
        agent: str | None = None,
    ) -> int:
        return len(
            self.filter(
                event_type=event_type,
                agent=agent,
            )
    )
