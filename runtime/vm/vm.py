from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable

from compiler.ir import (
    IRAgent,
    IRBehavior,
    IRFunction,
    IRModule,
    OpCode,
)

from .frame import CallFrame
from .messaging import (
    AgentMessage,
    MessageBus,
)
from .scheduler import Scheduler


class VMError(Exception):
    """Raised when the CARDINAL VM encounters an execution error."""


class AgentLifecycle(Enum):
    """Lifecycle states of a CARDINAL agent."""

    CREATED = auto()
    RUNNING = auto()
    STOPPED = auto()


@dataclass(frozen=True)
class AgentEvent:
    """Event delivered to a CARDINAL agent."""

    type: str
    payload: object | None = None
    source: str | None = None


@dataclass
class AgentContext:
    """Runtime context owned by an agent instance."""

    lifecycle: AgentLifecycle = (
        AgentLifecycle.CREATED
    )

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

    def grant(
        self,
        capability: str,
    ) -> None:
        if not capability:
            raise VMError(
                "Capability name cannot be empty."
            )

        self.capabilities.add(
            capability
        )

    def revoke(
        self,
        capability: str,
    ) -> None:
        self.capabilities.discard(
            capability
        )

    def has_capability(
        self,
        capability: str,
    ) -> bool:
        return capability in self.capabilities

    def require_capability(
        self,
        capability: str,
    ) -> None:
        if not self.has_capability(
            capability
        ):
            raise VMError(
                f"Agent lacks capability: "
                f"{capability}"
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

        self.behavior_bindings[
            event_type
        ] = behavior_name

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
                f"Agent '{self.name}' "
                "cannot be restarted."
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


class VM:
    """Stack-based virtual machine for CARDINAL IR."""

    def __init__(self) -> None:
        self.frames: list[CallFrame] = []
        self.return_value: object | None = None

        self.agents: list[AgentInstance] = []
        self.current_agent: AgentInstance | None = None

        self.message_bus = MessageBus()
        self.scheduler = Scheduler()

        self._instruction_budget: int | None = None

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    def execute(
        self,
        function: IRFunction,
        module: IRModule | None = None,
    ) -> object | None:
        self.frames.clear()
        self.return_value = None
        self.current_agent = None
        self._instruction_budget = None

        frame = CallFrame(
            function_name=function.name
        )

        self.frames.append(frame)

        result = self._execute_function(
            function,
            module,
            frame,
        )

        self.return_value = result
        self.frames.clear()

        return result

    # ------------------------------------------------------------------
    # Agent lifecycle
    # ------------------------------------------------------------------

    def spawn_agent(
        self,
        agent: IRAgent,
    ) -> AgentInstance:
        instance = AgentInstance(
            agent
        )

        self.agents.append(
            instance
        )

        self.message_bus.register(
            instance.name
        )

        self.scheduler.register(
            instance.name
        )

        return instance

    def spawn_agent_by_name(
        self,
        module: IRModule,
        name: str,
    ) -> AgentInstance:
        agent = module.get_agent(
            name
        )

        if agent is None:
            raise VMError(
                f"Unknown agent: {name}"
            )

        return self.spawn_agent(
            agent
        )

    def start_agent(
        self,
        instance: AgentInstance,
    ) -> AgentInstance:
        instance.start()

        return instance

    def stop_agent(
        self,
        instance: AgentInstance,
    ) -> None:
        instance.stop()

        self.scheduler.unregister(
            instance.name
        )

    def get_agent(
        self,
        name: str,
    ) -> AgentInstance | None:
        for agent in self.agents:
            if agent.name == name:
                return agent

        return None

    # ------------------------------------------------------------------
    # Capabilities
    # ------------------------------------------------------------------

    def grant_capability(
        self,
        instance: AgentInstance,
        capability: str,
    ) -> None:
        instance.context.grant(
            capability
        )

    def revoke_capability(
        self,
        instance: AgentInstance,
        capability: str,
    ) -> None:
        instance.context.revoke(
            capability
        )

    def require_capability(
        self,
        instance: AgentInstance,
        capability: str,
    ) -> None:
        instance.context.require_capability(
            capability
        )

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def remember(
        self,
        instance: AgentInstance,
        key: str,
        value: object,
    ) -> None:
        instance.remember(
            key,
            value,
        )

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
        instance.forget(
            key
        )

    # ------------------------------------------------------------------
    # Event system
    # ------------------------------------------------------------------

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
        instance.emit(
            event
        )

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
            instance.start()

        behavior_name = (
            instance.context.resolve_behavior(
                event
            )
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

        result = self.execute_behavior(
            instance,
            behavior_name,
            module,
        )

        instance.context.events_processed += 1

        return result

    def process_next_event(
        self,
        instance: AgentInstance,
        module: IRModule | None = None,
    ) -> object | None:
        if not instance.event_queue:
            return None

        event = instance.event_queue.pop(
            0
        )

        return self.dispatch_event(
            instance,
            event,
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

    # ------------------------------------------------------------------
    # Agent-to-agent messaging
    # ------------------------------------------------------------------

    def send_message(
        self,
        sender: AgentInstance,
        recipient: AgentInstance | str,
        message_type: str,
        payload: object | None = None,
        metadata: dict[str, object] | None = None,
    ) -> AgentMessage:
        """
        Send a message from one agent to another.

        Messaging requires the sender to have the
        'messaging.send' capability.
        """

        sender.context.require_capability(
            "messaging.send"
        )

        if isinstance(
            recipient,
            AgentInstance,
        ):
            recipient_name = recipient.name
        else:
            recipient_name = recipient

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
            metadata=dict(
                metadata or {}
            ),
        )

        self.message_bus.send(
            message
        )

        sender.context.messages_sent += 1

        return message

    def receive_message(
        self,
        receiver: AgentInstance,
    ) -> AgentMessage | None:
        """
        Receive one message for an agent.

        Receiving requires 'messaging.receive'.
        """

        receiver.context.require_capability(
            "messaging.receive"
        )

        message = self.message_bus.receive(
            receiver.name
        )

        if message is not None:
            receiver.context.messages_received += 1

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

        return messages

    def pending_messages(
        self,
        instance: AgentInstance,
    ) -> int:
        return self.message_bus.pending(
            instance.name
        )

    # ------------------------------------------------------------------
    # Message -> Event bridge
    # ------------------------------------------------------------------

    def dispatch_message(
        self,
        receiver: AgentInstance,
        message: AgentMessage,
        module: IRModule | None = None,
    ) -> object | None:
        """
        Convert a message into an AgentEvent and dispatch it.

        The message payload and sender are preserved.
        """

        event = AgentEvent(
            type=message.type,
            payload=message.payload,
            source=message.sender,
        )

        return self.dispatch_event(
            receiver,
            event,
            module,
        )

    def process_next_message(
        self,
        receiver: AgentInstance,
        module: IRModule | None = None,
    ) -> object | None:
        message = self.receive_message(
            receiver
        )

        if message is None:
            return None

        return self.dispatch_message(
            receiver,
            message,
            module,
        )

    # ------------------------------------------------------------------
    # Scheduler
    # ------------------------------------------------------------------

    def tick(
        self,
        module: IRModule | None = None,
    ) -> bool:
        """
        Execute one scheduler tick.

        Returns True if work was processed.
        """

        self.scheduler.tick()

        agent_name = (
            self.scheduler.next_agent()
        )

        if agent_name is None:
            return False

        agent = self.get_agent(
            agent_name
        )

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
            )
            > 0
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
        """
        Run the cooperative scheduler.

        Returns the number of ticks executed.
        """

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

    # ------------------------------------------------------------------
    # Behavior execution
    # ------------------------------------------------------------------

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
            instance.start()

        self.frames.clear()
        self.return_value = None
        self.current_agent = instance

        self._instruction_budget = (
            instance.context.max_instructions
        )

        frame = CallFrame(
            function_name=(
                f"{instance.name}."
                f"{behavior_name}"
            ),
            locals=dict(
                instance.state
            ),
        )

        self.frames.append(frame)

        result = self._execute_behavior(
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

        self.frames.clear()
        self.current_agent = None
        self._instruction_budget = None

        return result

    # ------------------------------------------------------------------
    # Internal execution
    # ------------------------------------------------------------------

    def _execute_function(
        self,
        function: IRFunction,
        module: IRModule | None,
        frame: CallFrame,
    ) -> object | None:
        return self._execute_instructions(
            function.instructions,
            module,
            frame,
        )

    def _execute_behavior(
        self,
        behavior: IRBehavior,
        module: IRModule | None,
        frame: CallFrame,
    ) -> object | None:
        return self._execute_instructions(
            behavior.instructions,
            module,
            frame,
        )

    def _execute_instructions(
        self,
        instructions,
        module: IRModule | None,
        frame: CallFrame,
    ) -> object | None:
        while (
            frame.instruction_pointer
            < len(instructions)
        ):
            self._consume_instruction_budget()

            instruction = instructions[
                frame.instruction_pointer
            ]

            opcode = instruction.opcode
            stack = frame.operand_stack

            if opcode == OpCode.CONSTANT:
                stack.append(
                    instruction.operand
                )

            elif opcode == OpCode.LOAD:
                name = instruction.operand

                if not isinstance(name, str):
                    raise VMError(
                        "LOAD requires a variable name"
                    )

                try:
                    value = frame.lookup(name)
                except KeyError as exc:
                    raise VMError(
                        f"Undefined variable: {name}"
                    ) from exc

                stack.append(value)

            elif opcode == OpCode.STORE:
                if not stack:
                    raise VMError(
                        "Stack underflow during STORE"
                    )

                name = instruction.operand

                if not isinstance(name, str):
                    raise VMError(
                        "STORE requires a variable name"
                    )

                frame.declare(
                    name,
                    stack.pop(),
                )

            elif opcode == OpCode.ASSIGN:
                if not stack:
                    raise VMError(
                        "Stack underflow during ASSIGN"
                    )

                name = instruction.operand

                if not isinstance(name, str):
                    raise VMError(
                        "ASSIGN requires a variable name"
                    )

                value = stack.pop()

                frame.assign(
                    name,
                    value,
                )

            elif opcode == OpCode.ENTER_SCOPE:
                frame.enter_scope()

            elif opcode == OpCode.EXIT_SCOPE:
                try:
                    frame.exit_scope()
                except RuntimeError as exc:
                    raise VMError(
                        str(exc)
                    ) from exc

            elif opcode == OpCode.ADD:
                self._binary(
                    frame,
                    lambda a, b: a + b,
                )

            elif opcode == OpCode.SUB:
                self._binary(
                    frame,
                    lambda a, b: a - b,
                )

            elif opcode == OpCode.MUL:
                self._binary(
                    frame,
                    lambda a, b: a * b,
                )

            elif opcode == OpCode.DIV:
                self._binary(
                    frame,
                    lambda a, b: a / b,
                )

            elif opcode == OpCode.MOD:
                self._binary(
                    frame,
                    lambda a, b: a % b,
                )

            elif opcode == OpCode.NEGATE:
                if not stack:
                    raise VMError(
                        "Stack underflow during NEGATE"
                    )

                value = stack.pop()

                try:
                    stack.append(-value)
                except Exception as exc:
                    raise VMError(
                        f"Unary negation failed: {exc}"
                    ) from exc

            elif opcode == OpCode.NOT:
                if not stack:
                    raise VMError(
                        "Stack underflow during NOT"
                    )

                value = stack.pop()
                stack.append(not value)

            elif opcode == OpCode.EQUAL:
                self._binary(
                    frame,
                    lambda a, b: a == b,
                )

            elif opcode == OpCode.NOT_EQUAL:
                self._binary(
                    frame,
                    lambda a, b: a != b,
                )

            elif opcode == OpCode.LESS:
                self._binary(
                    frame,
                    lambda a, b: a < b,
                )

            elif opcode == OpCode.LESS_EQUAL:
                self._binary(
                    frame,
                    lambda a, b: a <= b,
                )

            elif opcode == OpCode.GREATER:
                self._binary(
                    frame,
                    lambda a, b: a > b,
                )

            elif opcode == OpCode.GREATER_EQUAL:
                self._binary(
                    frame,
                    lambda a, b: a >= b,
                )

            elif opcode == OpCode.AND:
                self._binary(
                    frame,
                    lambda a, b: a and b,
                )

            elif opcode == OpCode.OR:
                self._binary(
                    frame,
                    lambda a, b: a or b,
                )

            elif opcode == OpCode.CALL:
                result = self._call(
                    instruction,
                    module,
                    frame,
                )

                if result is not None:
                    stack.append(result)

            elif opcode == OpCode.CALL_AGENT:
                result = self._call_agent(
                    instruction,
                    module,
                    frame,
                )

                if result is not None:
                    stack.append(result)

            elif opcode == OpCode.JUMP:
                frame.instruction_pointer = int(
                    instruction.operand
                )
                continue

            elif opcode == OpCode.JUMP_IF_FALSE:
                if not stack:
                    raise VMError(
                        "Stack underflow during "
                        "JUMP_IF_FALSE"
                    )

                condition = stack.pop()

                if not condition:
                    frame.instruction_pointer = int(
                        instruction.operand
                    )
                    continue

            elif opcode == OpCode.RETURN:
                result = (
                    stack.pop()
                    if stack
                    else None
                )

                frame.return_value = result

                if (
                    self.frames
                    and self.frames[-1] is frame
                ):
                    self.frames.pop()

                return result

            elif opcode == OpCode.HALT:
                return None

            else:
                raise VMError(
                    f"Unsupported opcode: "
                    f"{opcode.name}"
                )

            frame.instruction_pointer += 1

        return frame.return_value

    # ------------------------------------------------------------------
    # Function calls
    # ------------------------------------------------------------------

    def _call(
        self,
        instruction,
        module: IRModule | None,
        caller_frame: CallFrame,
    ) -> object | None:
        if module is None:
            raise VMError(
                "CALL requires an IR module."
            )

        function_name = instruction.operand

        if not isinstance(
            function_name,
            str,
        ):
            raise VMError(
                "CALL requires a function name"
            )

        target = module.get_function(
            function_name
        )

        if target is None:
            raise VMError(
                f"Unknown function: "
                f"{function_name}"
            )

        return self._invoke_function(
            target,
            module,
            caller_frame,
        )

    def _call_agent(
        self,
        instruction,
        module: IRModule | None,
        caller_frame: CallFrame,
    ) -> object | None:
        if self.current_agent is None:
            raise VMError(
                "CALL_AGENT requires an active agent."
            )

        function_name = instruction.operand

        if not isinstance(
            function_name,
            str,
        ):
            raise VMError(
                "CALL_AGENT requires a function name"
            )

        target = self.current_agent.get_function(
            function_name
        )

        if target is None:
            raise VMError(
                f"Unknown agent function: "
                f"{self.current_agent.name}."
                f"{function_name}"
            )

        result = self._invoke_function(
            target,
            module,
            caller_frame,
        )

        for name, value in (
            self.current_agent.state.items()
        ):
            if name in caller_frame.locals:
                caller_frame.locals[name] = value

        return result

            def _invoke_function(
        self,
        target: IRFunction,
        module: IRModule | None,
        caller_frame: CallFrame,
    ) -> object | None:
        argument_count = len(
            target.parameters
        )

        if (
            len(caller_frame.operand_stack)
            < argument_count
        ):
            raise VMError(
                f"Not enough arguments for "
                f"function '{target.name}'"
            )

        if argument_count == 0:
            arguments = []
        else:
            arguments = (
                caller_frame.operand_stack[
                    -argument_count:
                ]
            )

        function_locals = dict(
            zip(
                target.parameters,
                arguments,
            )
        )

        if self.current_agent is not None:
            for name, value in (
                self.current_agent.state.items()
            ):
                function_locals.setdefault(
                    name,
                    value,
                )

        frame = CallFrame(
            function_name=target.name,
            locals=function_locals,
        )

        self.frames.append(frame)

        result = self._execute_function(
            target,
            module,
            frame,
        )

        if self.current_agent is not None:
            for name in self.current_agent.state:
                if name in frame.locals:
                    self.current_agent.state[
                        name
                    ] = frame.locals[name]

        if self.frames and self.frames[-1] is frame:
            self.frames.pop()

        return result

    # ------------------------------------------------------------------
    # Runtime safety
    # ------------------------------------------------------------------

    def _consume_instruction_budget(self) -> None:
        if self.current_agent is None:
            return

        self.current_agent.context.instructions_executed += 1

        limit = self._instruction_budget

        if limit is None:
            return

        if (
            self.current_agent.context.instructions_executed
            > limit
        ):
            raise VMError(
                f"Instruction limit exceeded "
                f"for agent '{self.current_agent.name}'."
            )

    # ------------------------------------------------------------------
    # Arithmetic / logical operations
    # ------------------------------------------------------------------

    def _binary(
        self,
        frame: CallFrame,
        operation: Callable[[object, object], object],
    ) -> None:
        stack = frame.operand_stack

        if len(stack) < 2:
            raise VMError(
                "Stack underflow during "
                "binary operation"
            )

        right = stack.pop()
        left = stack.pop()

        try:
            result = operation(
                left,
                right,
            )
        except Exception as exc:
            raise VMError(
                f"Binary operation failed: {exc}"
            ) from exc

        stack.append(result)
