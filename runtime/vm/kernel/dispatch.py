from __future__ import annotations

from compiler.ir import IRModule

from ..agents import AgentEvent, AgentInstance, AgentLifecycle
from ..messaging import AgentMessage
from .errors import VMError


class DispatchEngine:
    """Handles event and message dispatch for the VM."""

    def __init__(self, vm) -> None:
        self.vm = vm

    def dispatch_event(
        self,
        instance: AgentInstance,
        event: AgentEvent,
        module: IRModule | None = None,
    ) -> object | None:
        if (
            instance.context.lifecycle
            == AgentLifecycle.STOPPED
        ):
            raise VMError(
                f"Agent '{instance.name}' is stopped."
            )

        if (
            instance.context.lifecycle
            == AgentLifecycle.CREATED
        ):
            self.vm.start_agent(instance)

        behavior_name = (
            instance.context.resolve_behavior(event)
        )

        if behavior_name is None:
            return None

        behavior = instance.get_behavior(
            behavior_name
        )

        if behavior is None:
            raise VMError(
                f"No behavior '{behavior_name}' "
                f"for event '{event.type}' "
                f"on agent '{instance.name}'"
            )

        previous_event = (
            instance.context.current_event
        )

        instance.context.current_event = event

        try:
            result = self.vm.execute_behavior(
                instance,
                behavior_name,
                module,
            )

            instance.context.events_processed += 1

            self.vm._record_runtime_event(
                "event.processed",
                agent=instance,
                behavior=behavior_name,
                source=event.source,
                metadata={
                    "event_type": event.type
                },
            )

            return result

        finally:
            instance.context.current_event = (
                previous_event
            )

    def process_next_event(
        self,
        instance: AgentInstance,
        module: IRModule | None = None,
    ) -> object | None:
        if not instance.event_queue:
            return None

        event = instance.event_queue.pop(0)

        return self.dispatch_event(
            instance,
            event,
            module,
        )

    def dispatch_message(
        self,
        receiver: AgentInstance,
        message: AgentMessage,
        module: IRModule | None = None,
    ) -> object | None:
        event = AgentEvent(
            type=message.type,
            payload=message.payload,
            source=message.sender,
        )

        previous_message = (
            receiver.context.current_message
        )

        receiver.context.current_message = message

        try:
            return self.dispatch_event(
                receiver,
                event,
                module,
            )
        finally:
            receiver.context.current_message = (
                previous_message
            )

    def process_next_message(
        self,
        receiver: AgentInstance,
        module: IRModule | None = None,
    ) -> object | None:
        message = self.vm.receive_message(receiver)

        if message is None:
            return None

        return self.dispatch_message(
            receiver,
            message,
            module,
        )
