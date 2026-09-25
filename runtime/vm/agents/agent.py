from __future__ import annotations

from dataclasses import dataclass, field

from compiler.ir import IRAgent, IRBehavior, IRFunction

from ..kernel.errors import VMError
from .context import AgentContext
from .events import AgentEvent
from .lifecycle import AgentLifecycle


@dataclass
class AgentInstance:
    """Runtime instance of a CARDINAL agent."""

    agent: IRAgent

    state: dict[str, object] = field(
        default_factory=dict
    )

    context: AgentContext = field(
        default_factory=AgentContext
    )

    event_queue: list[AgentEvent] = field(
        default_factory=list
    )

    memory: dict[str, object] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.state:
            self.state = dict(
                self.agent.initial_state
            )

        for name in self.agent.state:
            self.state.setdefault(
                name,
                None,
            )

    @property
    def name(self) -> str:
        return self.agent.name

    @property
    def lifecycle(self) -> AgentLifecycle:
        return self.context.lifecycle

    def get_behavior(
        self,
        name: str,
    ) -> IRBehavior | None:
        return self.agent.get_behavior(name)

    def get_function(
        self,
        name: str,
    ) -> IRFunction | None:
        return self.agent.get_function(name)

    def start(self) -> None:
        if (
            self.context.lifecycle
            == AgentLifecycle.STOPPED
        ):
            raise VMError(
                f"Agent '{self.name}' cannot be restarted."
            )

        self.context.lifecycle = (
            AgentLifecycle.RUNNING
        )

    def stop(self) -> None:
        self.context.lifecycle = (
            AgentLifecycle.STOPPED
        )

        self.event_queue.clear()

    def emit(
        self,
        event: AgentEvent,
    ) -> None:
        if (
            self.context.lifecycle
            == AgentLifecycle.STOPPED
        ):
            raise VMError(
                f"Agent '{self.name}' is stopped."
            )

        self.event_queue.append(event)

    def remember(
        self,
        key: str,
        value: object,
    ) -> None:
        if not key:
            raise VMError(
                "Memory key cannot be empty."
            )

        self.memory[key] = value

    def recall(
        self,
        key: str,
        default: object | None = None,
    ) -> object | None:
        return self.memory.get(
            key,
            default,
        )

    def forget(
        self,
        key: str,
    ) -> None:
        self.memory.pop(
            key,
            None,
      )
