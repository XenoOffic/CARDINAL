from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Iterable

from compiler.ir import (
    IRAgent,
    IRBehavior,
    IRFunction,
    IRModule,
    OpCode,
)

from .frame import CallFrame


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
    """
    Runtime context owned by an agent instance.

    The context contains runtime-only information such as
    capabilities, lifecycle state and execution limits.
    """

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

    def grant(self, capability: str) -> None:
        """Grant a capability to the agent."""
        if not capability:
            raise VMError(
                "Capability name cannot be empty."
            )

        self.capabilities.add(capability)

    def revoke(self, capability: str) -> None:
        """Revoke a capability from the agent."""
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
                f"Agent lacks capability: "
                f"{capability}"
            )

    def bind_event(
        self,
        event_type: str,
        behavior_name: str,
    ) -> None:
        """Bind an event type to an agent behavior."""

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
        """
        Resolve the behavior associated with an event.

        Explicit event bindings have priority. If none
        exists, the event type itself is treated as the
        behavior name.
        """

        behavior = self.behavior_bindings.get(
            event.type
        )

        if behavior is not None:
            return behavior

        return event.type

    def reset_counters(self) -> None:
        self.events_processed = 0
        self.instructions_executed = 0


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
        """Move the agent into the RUNNING state."""

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
        """Stop the agent and clear pending events."""

        self.context.lifecycle = (
            AgentLifecycle.STOPPED
        )

        self.event_queue.clear()

    def emit(
        self,
        event: AgentEvent,
    ) -> None:
        """Queue an event for this agent."""

        if (
            self.context.lifecycle
            == AgentLifecycle.STOPPED
        ):
            raise VMError(
                f"Agent '{self.name}' is stopped."
            )

        self.event_queue.append(event)


class VM:
    """Stack-based virtual machine for CARDINAL IR."""

    def __init__(self) -> None:
        self.frames: list[CallFrame] = []
        self.return_value: object | None = None

        self.agents: list[AgentInstance] = []

        self.current_agent: AgentInstance | None = None

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
        """
        Create a runtime instance of an agent.

        Newly spawned agents start in CREATED state.
        """

        instance = AgentInstance(agent)

        self.agents.append(instance)

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
        """Start an agent."""

        instance.start()

        return instance

    def stop_agent(
        self,
        instance: AgentInstance,
    ) -> None:
        """Stop an agent."""

        instance.stop()

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
    # Event system
    # ------------------------------------------------------------------

    def bind_behavior(
        self,
        instance: AgentInstance,
        event_type: str,
        behavior_name: str,
    ) -> None:
        """
        Bind an event type to a behavior.

        Example:

            vm.bind_behavior(
                agent,
                "tick",
                "update",
            )
        """

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
        """
        Emit an event into an agent's event queue.
        """

        instance.emit(event)

    def dispatch_event(
        self,
        instance: AgentInstance,
        event: AgentEvent,
        module: IRModule | None = None,
    ) -> object | None:
        """
        Observe an event, resolve its behavior and execute it.
        """

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
        """
        Process one pending event.

        Returns the behavior result or None when the
        queue is empty.
        """

        if not instance.event_queue:
            return None

        event = instance.event_queue.pop(0)

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
        """
        Process queued events until the agent becomes idle.

        max_events prevents unbounded event processing.
        """

        if max_events is not None and max_events < 0:
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

            del caller_frame.operand_stack[
                -argument_count:
            ]

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
                    self.current_agent.state[name] = (
                        frame.locals[name]
                    )

        return result

    # ------------------------------------------------------------------
    # Runtime safety
    # ------------------------------------------------------------------

    def _consume_instruction_budget(self) -> None:
        """
        Consume one instruction from the active agent budget.

        None means unlimited.
        """

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
