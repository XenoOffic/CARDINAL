from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentEvent:
    """Event delivered to a CARDINAL agent."""

    type: str
    payload: object | None = None
    source: str | None = None
