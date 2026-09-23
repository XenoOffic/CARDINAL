from __future__ import annotations

from dataclasses import dataclass, field

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


@dataclass
class AgentInstance:
    """Runtime instance of a CARDINAL agent."""

    agent: IRAgent

    state: dict[str, object] = field(
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


class VM:
    """Stack-based virtual machine for CARDINAL IR."""

    def __init__(self) -> None:
        self.frames: list[CallFrame] = []
        self.return_value: object | None = None
        self.agents: list[AgentInstance] = []
        self.current_agent: AgentInstance | None = None

    def execute(
        self,
        function: IRFunction,
        module: IRModule | None = None,
    ) -> object | None:
        self.frames.clear()
        self.return_value = None
        self.current_agent = None

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

    def spawn_agent(
        self,
        agent: IRAgent,
    ) -> AgentInstance:
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

        self.frames.clear()
        self.return_value = None
        self.current_agent = instance

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

        # The behavior frame may have modified agent
        # state directly. Synchronize only the values
        # that were actually present in the frame.
        #
        # Agent functions synchronize their changes
        # directly into instance.state, and _call_agent
        # mirrors those changes back into this frame.
        for name in instance.state:
            if name in frame.locals:
                instance.state[name] = frame.locals[name]

        self.return_value = result
        self.frames.clear()
        self.current_agent = None

        return result

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

        # The agent function is authoritative for
        # agent state. Mirror the updated state back
        # into the caller frame so subsequent behavior
        # instructions see the new values.
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

        # Agent functions receive a snapshot of the
        # current agent state as their initial locals.
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

        # Persist modifications made by an agent
        # function back into the actual agent instance.
        if self.current_agent is not None:
            for name in self.current_agent.state:
                if name in frame.locals:
                    self.current_agent.state[name] = (
                        frame.locals[name]
                    )

        return result

    def _binary(
        self,
        frame: CallFrame,
        operation,
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
