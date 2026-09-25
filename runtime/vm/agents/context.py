from __future__ import annotations

from dataclasses import dataclass, field

from ..kernel.errors import VMError
from ..messaging import AgentMessage
from .events import AgentEvent
from .lifecycle import AgentLifecycle


@dataclass
class AgentContext:
    """Runtime context owned by an agent instance."""

    lifecycle: AgentLifecycle = AgentLifecycle.CREATED

    capabilities: set[str] = field(
        default_factory=set
    )

    max_instructions: int | None = None

    behavior_bindings: dict[str, str] = field(
        default_factory=dict
    )

    events_processed: int = 0
    instructions_executed: int = 0

    messages_sent: int = 0
    messages_received: int = 0

    current_behavior: str | None = None
    current_event: AgentEvent | None = None
    current_message: AgentMessage | None = None

    execution_depth: int = 0
    last_error: str | None = None

    def grant(
        self,
        capability: str,
    ) -> None:
        if not capability:
            raise VMError(
                "Capability name cannot be empty."
            )

        self.capabilities.add(capability)

    def revoke(
        self,
        capability: str,
    ) -> None:
        self.capabilities.discard(capability)

    def has_capability(
        self,
        capability: str,
    ) -> bool:
        return capability in self.capabilities

    def require_capability(
        self,
        capability: str,
    ) -> None:
        if not self.has_capability(capability):
            raise VMError(
                f"Agent lacks capability: {capability}"
            )

    def bind_event(
        self,
        event_type: str,
        behavior_name: str,
    ) -> None:
        if not event_type:
            raise VMError(
                "Event type cannot be empty."
            )

        if not behavior_name:
            raise VMError(
                "Behavior name cannot be empty."
            )

        self.behavior_bindings[event_type] = (
            behavior_name
        )

    def resolve_behavior(
        self,
        event: AgentEvent,
    ) -> str | None:
        behavior = self.behavior_bindings.get(
            event.type
        )

        if behavior is not None:
            return behavior

        return event.type

    def reset_counters(self) -> None:
        self.events_processed = 0
        self.instructions_executed = 0
        self.messages_sent = 0
        self.messages_received = 0

        self.current_behavior = None
        self.current_event = None
        self.current_message = None

        self.execution_depth = 0
        self.last_error = None
