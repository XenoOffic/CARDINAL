from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentMessage:
    """Message exchanged between CARDINAL agents."""

    sender: str
    recipient: str
    type: str
    payload: object | None = None
    metadata: dict[str, object] = field(
        default_factory=dict
    )


class MessageBus:
    """
    Runtime message bus for CARDINAL agents.

    Messages are queued and delivered explicitly by the
    scheduler/runtime. The bus itself does not execute code.
    """

    def __init__(self) -> None:
        self._queues: dict[str, list[AgentMessage]] = {}
        self._history: list[AgentMessage] = []

    @property
    def history(self) -> list[AgentMessage]:
        """Return a copy of the message history."""
        return list(self._history)

    def register(self, agent_name: str) -> None:
        if not agent_name:
            raise ValueError(
                "Agent name cannot be empty."
            )

        self._queues.setdefault(
            agent_name,
            [],
        )

    def unregister(self, agent_name: str) -> None:
        self._queues.pop(
            agent_name,
            None,
        )

    def send(
        self,
        message: AgentMessage,
    ) -> None:
        if not message.sender:
            raise ValueError(
                "Message sender cannot be empty."
            )

        if not message.recipient:
            raise ValueError(
                "Message recipient cannot be empty."
            )

        if not message.type:
            raise ValueError(
                "Message type cannot be empty."
            )

        self.register(message.recipient)

        self._queues[
            message.recipient
        ].append(message)

        self._history.append(message)

    def receive(
        self,
        agent_name: str,
    ) -> AgentMessage | None:
        queue = self._queues.get(
            agent_name
        )

        if not queue:
            return None

        return queue.pop(0)

    def receive_all(
        self,
        agent_name: str,
    ) -> list[AgentMessage]:
        queue = self._queues.get(
            agent_name
        )

        if not queue:
            return []

        messages = list(queue)
        queue.clear()

        return messages

    def pending(
        self,
        agent_name: str,
    ) -> int:
        return len(
            self._queues.get(
                agent_name,
                [],
            )
        )

    def total_pending(self) -> int:
        return sum(
            len(queue)
            for queue in self._queues.values()
        )

    def clear(self) -> None:
        for queue in self._queues.values():
            queue.clear()

        self._history.clear()
