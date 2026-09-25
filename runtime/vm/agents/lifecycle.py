from __future__ import annotations

from enum import Enum, auto


class AgentLifecycle(Enum):
    """Lifecycle states of a CARDINAL agent."""

    CREATED = auto()
    RUNNING = auto()
    STOPPED = auto()
