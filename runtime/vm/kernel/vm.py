from __future__ import annotations

from compiler.ir import IRAgent, IRFunction, IRModule

from ..agents import (
    AgentEvent,
    AgentInstance,
    AgentLifecycle,
)
from ..intelligence import RuntimeIntelligence
from ..messaging import AgentMessage, MessageBus
from ..observability import RuntimeHistory
from ..scheduler import Scheduler
from .calls import CallExecutor
from .dispatch import DispatchEngine
from .errors import VMError
from .execution import ExecutionEngine
from .frame import CallFrame
from .limits import ExecutionLimits


class VM:
    """Stack-based virtual machine for CARDINAL IR."""

    def __init__(self) -> None:
        self.frames: list[CallFrame] = []
        self.return_value: object | None = None

        self.agents: list[AgentInstance] = []
        self.current_agent: AgentInstance | None = None

        self.message_bus = MessageBus()
        self.scheduler = Scheduler()

        self.observability = RuntimeHistory()
        self.intelligence = RuntimeIntelligence(
            self.observability
        )

        self.limits = ExecutionLimits()

        self._instruction_budget: int | None = None
        self._execution_instruction_count = 0

        self.execution = ExecutionEngine(self)
        self.calls = CallExecutor(self)
        self.dispatch = DispatchEngine(self)

    def _record_runtime_event(
        self,
        event_type: str,
        *,
        agent: AgentInstance | None = None,
        behavior: str | None = None,
        source: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.observability.record(
            event_type,
            agent=(
                agent.name
                if agent is not None
                else None
            ),
            behavior=behavior,
            source=source,
            metadata=metadata,
        )

    def runtime_snapshot(self):
        return self.intelligence.snapshot()

    def agent_statistics(
        self,
        agent_name: str,
    ):
        return self.intelligence.agent_statistics(
            agent_name
        )

    def behavior_statistics(
        self,
        behavior_name: str,
    ):
        return self.intelligence.behavior_statistics(
            behavior_name
        )

    def recent_errors(
        self,
        limit: int = 10,
    ):
        return self.intelligence.recent_errors(
            limit
        )

    def detect_runtime_patterns(self):
        return self.intelligence.detect_patterns()

    def execute(
        self,
        function: IRFunction,
        module: IRModule | None = None,
    ) -> object | None:
        self.frames.clear()
        self.return_value = None
        self.current_agent = None

        self._instruction_budget = None
        self._execution_instruction_count = 0
        self.limits.set_budget(None)

        frame = CallFrame(
            function_name=function.name
        )

        self.frames.append(frame)

        try:
            result = self.execution.execute_function(
                function,
                module,
                frame,
            )
        except Exception as exc:
            self._record_runtime_event(
                "runtime.error",
                metadata={
                    "error": str(exc),
                    "function": function.name,
                },
            )
            raise
        finally:
            self.frames.clear()
            self.current_agent = None

            self._instruction_budget = None
            self._execution_instruction_count = 0
            self.limits.set_budget(None)

        self.return_value = result

        return result

    def spawn_agent(
        self,
        agent: IRAgent,
    ) -> AgentInstance:
        instance = AgentInstance(agent)

        self.agents.append(instance)

        self.message_bus.register(
            instance.name
        )

        self.scheduler.register(
            instance.name
        )

        self._record_runtime_event(
            "agent.spawned",
            agent=instance,
            metadata={
                "lifecycle": instance.lifecycle.name
            },
        )

        return instance

    def spawn_agent_by_name(
        self,
        module: IRModule,
        name: str,
    ) -> AgentInstance:
        agent = module.get_agent(name)

        if agent is None:
            raise VMError(
                f"Unknown agent: {name}"
            )

        return self.spawn_agent(agent)

    def start_agent(
        self,
        instance: AgentInstance,
    ) -> AgentInstance:
        instance.start()

        self._record_runtime_event(
            "agent.started",
            agent=instance,
            metadata={
                "lifecycle": instance.lifecycle.name
            },
        )

        return instance

    def stop_agent(
        self,
        instance: AgentInstance,
    ) -> None:
        instance.stop()

        self.scheduler.unregister(
            instance.name
        )

        self._record_runtime_event(
            "agent.stopped",
            agent=instance,
            metadata={
                "lifecycle": instance.lifecycle.name
            },
        )

    def get_agent(
        self,
        name: str,
    ) -> AgentInstance | None:
        for agent in self.agents:
            if agent.name == name:
                return agent

        return None

    def grant_capability(
        self,
        instance: AgentInstance,
        capability: str,
    ) -> None:
        instance.context.grant(capability)

    def revoke_capability(
        self,
        instance: AgentInstance,
        capability: str,
    ) -> None:
        instance.context.revoke(capability)

    def require_capability(
        self,
        instance: AgentInstance,
        capability: str,
    ) -> None:
        instance.context.require_capability(
            capability
        )

    def remember(
        self,
        instance: AgentInstance,
        key: str,
        value: object,
    ) -> None:
        instance.remember(key, value)

    def recall(
        self,
        instance: AgentInstance,
        key: str,
        default: object | None = None,
    ) -> object | None:
        return instance.recall(
            key,
            default,
        )

    def forget(
        self,
        instance: AgentInstance,
        key: str,
    ) -> None:
        instance.forget(key)

    def bind_behavior(
        self,
        instance: AgentInstance,
        event_type: str,
        behavior_name: str,
    ) -> None:
        behavior = instance.get_behavior(
            behavior_name
        )

        if behavior is None:
            raise VMError(
                f"Unknown behavior "
                f"'{behavior_name}' "
                f"for agent '{instance.name}'"
            )

        instance.context.bind_event(
            event_type,
            behavior_name,
        )

    def emit_event(
        self,
        instance: AgentInstance,
        event: AgentEvent,
    ) -> None:
        instance.emit(event)

    def dispatch_event(
        self,
        instance: AgentInstance,
        event: AgentEvent,
        module: IRModule | None = None,
    ) -> object | None:
        return self.dispatch.dispatch_event(
            instance,
            event,
            module,
        )

    def process_next_event(
        self,
        instance: AgentInstance,
        module: IRModule | None = None,
    ) -> object | None:
        return self.dispatch.process_next_event(
            instance,
            module,
        )

    def run_until_idle(
        self,
        instance: AgentInstance,
        module: IRModule | None = None,
        max_events: int | None = None,
    ) -> list[object | None]:
        if (
            max_events is not None
            and max_events < 0
        ):
            raise VMError(
                "max_events cannot be negative."
            )

        results: list[object | None] = []
        processed = 0

        while instance.event_queue:
            if (
                max_events is not None
                and processed >= max_events
            ):
                raise VMError(
                    "Event processing limit exceeded."
                )

            results.append(
                self.process_next_event(
                    instance,
                    module,
                )
            )

            processed += 1

        return results

    def send_message(
        self,
        sender: AgentInstance,
        recipient: AgentInstance | str,
        message_type: str,
        payload: object | None = None,
        metadata: dict[str, object] | None = None,
    ) -> AgentMessage:
        sender.context.require_capability(
            "messaging.send"
        )

        recipient_name = (
            recipient.name
            if isinstance(
                recipient,
                AgentInstance,
            )
            else recipient
        )

        target = self.get_agent(
            recipient_name
        )

        if target is None:
            raise VMError(
                f"Unknown recipient agent: "
                f"{recipient_name}"
            )

        message = AgentMessage(
            sender=sender.name,
            recipient=recipient_name,
            type=message_type,
            payload=payload,
            metadata=dict(metadata or {}),
        )

        self.message_bus.send(message)

        sender.context.messages_sent += 1

        self._record_runtime_event(
            "message.sent",
            agent=sender,
            source=sender.name,
            metadata={
                "recipient": recipient_name,
                "message_type": message_type,
            },
        )

        return message

    def receive_message(
        self,
        receiver: AgentInstance,
    ) -> AgentMessage | None:
        receiver.context.require_capability(
            "messaging.receive"
        )

        message = self.message_bus.receive(
            receiver.name
        )

        if message is not None:
            receiver.context.messages_received += 1

            self._record_runtime_event(
                "message.received",
                agent=receiver,
                source=message.sender,
                metadata={
                    "message_type": message.type,
                    "sender": message.sender,
                },
            )

        return message

    def receive_messages(
        self,
        receiver: AgentInstance,
    ) -> list[AgentMessage]:
        receiver.context.require_capability(
            "messaging.receive"
        )

        messages = self.message_bus.receive_all(
            receiver.name
        )

        receiver.context.messages_received += len(
            messages
        )

        for message in messages:
            self._record_runtime_event(
                "message.received",
                agent=receiver,
                source=message.sender,
                metadata={
                    "message_type": message.type,
                    "sender": message.sender,
                },
            )

        return messages

    def pending_messages(
        self,
        instance: AgentInstance,
    ) -> int:
        return self.message_bus.pending(
            instance.name
        )

    def dispatch_message(
        self,
        receiver: AgentInstance,
        message: AgentMessage,
        module: IRModule | None = None,
    ) -> object | None:
        return self.dispatch.dispatch_message(
            receiver,
            message,
            module,
        )

    def process_next_message(
        self,
        receiver: AgentInstance,
        module: IRModule | None = None,
    ) -> object | None:
        return self.dispatch.process_next_message(
            receiver,
            module,
        )

    def tick(
        self,
        module: IRModule | None = None,
    ) -> bool:
        self.scheduler.tick()

        def has_work(
            agent_name: str,
        ) -> bool:
            agent = self.get_agent(agent_name)

            if agent is None:
                return False

            if (
                agent.lifecycle
                != AgentLifecycle.RUNNING
            ):
                return False

            if agent.event_queue:
                return True

            return (
                self.message_bus.pending(
                    agent.name
                ) > 0
                and agent.context.has_capability(
                    "messaging.receive"
                )
            )

        agent_name = self.scheduler.next_agent(
            has_work
        )

        if agent_name is None:
            return False

        agent = self.get_agent(agent_name)

        if agent is None:
            return False

        if (
            agent.lifecycle
            != AgentLifecycle.RUNNING
        ):
            return False

        self.scheduler.stats.agents_scheduled += 1

        if agent.event_queue:
            self.process_next_event(
                agent,
                module,
            )

            self.scheduler.stats.events_processed += 1

            return True

        if (
            self.message_bus.pending(
                agent.name
            ) > 0
            and agent.context.has_capability(
                "messaging.receive"
            )
        ):
            self.process_next_message(
                agent,
                module,
            )

            self.scheduler.stats.messages_processed += 1

            return True

        return False

    def run_scheduler(
        self,
        module: IRModule | None = None,
        max_ticks: int = 100,
    ) -> int:
        if max_ticks < 0:
            raise VMError(
                "max_ticks cannot be negative."
            )

        executed = 0

        for _ in range(max_ticks):
            if not self.tick(module):
                break

            executed += 1

        return executed

    def execute_behavior(
        self,
        instance: AgentInstance,
        behavior_name: str,
        module: IRModule | None = None,
    ) -> object | None:
        behavior = instance.get_behavior(
            behavior_name
        )

        if behavior is None:
            raise VMError(
                f"Unknown behavior "
                f"'{behavior_name}' "
                f"for agent '{instance.name}'"
            )

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
            self.start_agent(instance)

        previous_agent = self.current_agent
        previous_budget = self._instruction_budget
        previous_count = (
            self._execution_instruction_count
        )
        previous_behavior = (
            instance.context.current_behavior
        )

        self.frames.clear()
        self.return_value = None
        self.current_agent = instance

        self._instruction_budget = (
            instance.context.max_instructions
        )

        self._execution_instruction_count = 0

        self.limits.set_budget(
            self._instruction_budget
        )

        instance.context.current_behavior = (
            behavior_name
        )

        instance.context.execution_depth += 1

        self._record_runtime_event(
            "behavior.started",
            agent=instance,
            behavior=behavior_name,
        )

        frame = CallFrame(
            function_name=(
                f"{instance.name}.{behavior_name}"
            ),
            locals=dict(instance.state),
        )

        self.frames.append(frame)

        try:
            result = self.execution.execute_behavior(
                behavior,
                module,
                frame,
            )

            for name in instance.state:
                if name in frame.locals:
                    instance.state[name] = (
                        frame.locals[name]
                    )

            self.return_value = result

            self._record_runtime_event(
                "behavior.completed",
                agent=instance,
                behavior=behavior_name,
                metadata={
                    "result_type": (
                        type(result).__name__
                        if result is not None
                        else "None"
                    )
                },
            )

            return result

        except Exception as exc:
            instance.context.last_error = str(exc)

            self._record_runtime_event(
                "runtime.error",
                agent=instance,
                behavior=behavior_name,
                metadata={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )

            raise

        finally:
            self.frames.clear()

            self.current_agent = previous_agent

            self._instruction_budget = (
                previous_budget
            )

            self._execution_instruction_count = (
                previous_count
            )

            self.limits.set_budget(
                previous_budget
            )

            instance.context.current_behavior = (
                previous_behavior
            )

            instance.context.execution_depth = max(
                0,
                instance.context.execution_depth - 1,
        )
