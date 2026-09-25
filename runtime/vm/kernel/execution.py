from __future__ import annotations

from typing import Any

from compiler.ir import IRBehavior, IRFunction, Instruction, OpCode

from .errors import VMError


class ExecutionEngine:
    """
    Core instruction execution engine for the CARDINAL VM.

    Responsibilities:
    - execute IR functions
    - execute IR behaviors
    - execute IR instruction streams
    - manage the operand stack
    - manage instruction pointers
    - enforce execution limits
    - perform primitive operations

    The engine intentionally contains no knowledge of:
    - evolution
    - hypotheses
    - experiments
    - decision making
    - orchestration
    """

    def __init__(self, vm: Any) -> None:
        self.vm = vm

    # ------------------------------------------------------------------
    # Public execution API
    # ------------------------------------------------------------------

    def execute_function(
        self,
        agent: Any,
        function: IRFunction,
        args: list[Any] | tuple[Any, ...],
    ) -> Any:
        """
        Execute an IR function through the VM call layer.
        """
        return self.vm.calls.invoke_function(
            agent,
            function,
            list(args),
        )

    def execute_behavior(
        self,
        agent: Any,
        behavior: IRBehavior,
    ) -> Any:
        """
        Execute an IR behavior.
        """
        return self.execute_instructions(
            agent,
            behavior.instructions,
        )

    def execute_instructions(
        self,
        agent: Any,
        instructions: list[Instruction] | tuple[Instruction, ...],
    ) -> Any:
        """
        Execute an instruction sequence.

        The instruction pointer is owned by this execution loop so that
        conditional and unconditional jumps remain local to the kernel.
        """
        instruction_stream = list(instructions)
        stack: list[Any] = []

        instruction_pointer = 0

        while instruction_pointer < len(instruction_stream):
            instruction = instruction_stream[instruction_pointer]

            self.consume_instruction(agent)

            result = self.execute_instruction(
                agent,
                instruction,
                stack,
            )

            if result[0] == "return":
                return result[1]

            if result[0] == "jump":
                instruction_pointer = result[1]
                continue

            if result[0] == "halt":
                return result[1]

            instruction_pointer += 1

        return None

    # ------------------------------------------------------------------
    # Instruction accounting
    # ------------------------------------------------------------------

    def consume_instruction(self, agent: Any) -> None:
        """
        Consume one instruction from the active execution budget.
        """
        self.vm.limits.consume()

        self.vm._execution_instruction_count += 1

        if agent is not None:
            agent.context.instructions_executed += 1

    # ------------------------------------------------------------------
    # Instruction dispatch
    # ------------------------------------------------------------------

    def execute_instruction(
        self,
        agent: Any,
        instruction: Instruction,
        stack: list[Any],
    ) -> tuple[str, Any]:
        """
        Execute one instruction.

        Returns:
            ("continue", None)
            ("return", value)
            ("jump", instruction_index)
            ("halt", value)
        """
        opcode = instruction.opcode
        operand = instruction.operand

        # --------------------------------------------------------------
        # Constants / variables
        # --------------------------------------------------------------

        if opcode == OpCode.CONSTANT:
            stack.append(operand)
            return ("continue", None)

        if opcode == OpCode.LOAD:
            value = agent.context.resolve_value(operand)
            stack.append(value)
            return ("continue", None)

        if opcode == OpCode.STORE:
            value = self._pop(stack)
            agent.context.assign_value(operand, value)
            return ("continue", None)

        if opcode == OpCode.ASSIGN:
            value = self._pop(stack)
            agent.context.assign_value(operand, value)
            stack.append(value)
            return ("continue", None)

        # --------------------------------------------------------------
        # Scope management
        # --------------------------------------------------------------

        if opcode == OpCode.ENTER_SCOPE:
            agent.context.enter_scope()
            return ("continue", None)

        if opcode == OpCode.EXIT_SCOPE:
            agent.context.exit_scope()
            return ("continue", None)

        # --------------------------------------------------------------
        # Arithmetic
        # --------------------------------------------------------------

        if opcode == OpCode.ADD:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(self.binary(opcode, left, right))
            return ("continue", None)

        if opcode == OpCode.SUB:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(self.binary(opcode, left, right))
            return ("continue", None)

        if opcode == OpCode.MUL:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(self.binary(opcode, left, right))
            return ("continue", None)

        if opcode == OpCode.DIV:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(self.binary(opcode, left, right))
            return ("continue", None)

        if opcode == OpCode.MOD:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(self.binary(opcode, left, right))
            return ("continue", None)

        if opcode == OpCode.NEGATE:
            value = self._pop(stack)
            stack.append(-value)
            return ("continue", None)

        # --------------------------------------------------------------
        # Logical / comparison operations
        # --------------------------------------------------------------

        if opcode == OpCode.NOT:
            value = self._pop(stack)
            stack.append(not value)
            return ("continue", None)

        if opcode == OpCode.EQUAL:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(left == right)
            return ("continue", None)

        if opcode == OpCode.NOT_EQUAL:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(left != right)
            return ("continue", None)

        if opcode == OpCode.LESS:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(left < right)
            return ("continue", None)

        if opcode == OpCode.LESS_EQUAL:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(left <= right)
            return ("continue", None)

        if opcode == OpCode.GREATER:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(left > right)
            return ("continue", None)

        if opcode == OpCode.GREATER_EQUAL:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(left >= right)
            return ("continue", None)

        if opcode == OpCode.AND:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(bool(left) and bool(right))
            return ("continue", None)

        if opcode == OpCode.OR:
            right = self._pop(stack)
            left = self._pop(stack)
            stack.append(bool(left) or bool(right))
            return ("continue", None)

        # --------------------------------------------------------------
        # Function calls
        # --------------------------------------------------------------

        if opcode == OpCode.CALL:
            function_name = self._require_operand(
                operand,
                "CALL requires a function name.",
            )

            function = agent.get_function(function_name)

            if function is None:
                raise VMError(
                    f"Function '{function_name}' not found for "
                    f"agent '{agent.agent.name}'."
                )

            argument_count = len(function.parameters)

            args = self._pop_arguments(
                stack,
                argument_count,
            )

            result = self.vm.calls.invoke_function(
                agent,
                function,
                args,
            )

            stack.append(result)

            return ("continue", None)

        if opcode == OpCode.CALL_AGENT:
            target = self._require_operand(
                operand,
                "CALL_AGENT requires a target.",
            )

            target_agent, function_name = self._resolve_agent_call(
                agent,
                target,
            )

            function = target_agent.get_function(function_name)

            if function is None:
                raise VMError(
                    f"Function '{function_name}' not found for "
                    f"agent '{target_agent.name}'."
                )

            argument_count = len(function.parameters)

            args = self._pop_arguments(
                stack,
                argument_count,
            )

            result = self.vm.calls.invoke_function(
                target_agent,
                function,
                args,
            )

            stack.append(result)

            return ("continue", None)

        # --------------------------------------------------------------
        # Control flow
        # --------------------------------------------------------------

        if opcode == OpCode.JUMP:
            target = self._require_jump_target(operand)

            return ("jump", target)

        if opcode == OpCode.JUMP_IF_FALSE:
            condition = self._pop(stack)

            if not condition:
                target = self._require_jump_target(operand)
                return ("jump", target)

            return ("continue", None)

        # --------------------------------------------------------------
        # Termination
        # --------------------------------------------------------------

        if opcode == OpCode.RETURN:
            if stack:
                return ("return", self._pop(stack))

            return ("return", None)

        if opcode == OpCode.HALT:
            if stack:
                return ("halt", self._pop(stack))

            return ("halt", None)

        raise VMError(
            f"Unsupported opcode: {opcode!r}"
        )

    # ------------------------------------------------------------------
    # Stack helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pop(stack: list[Any]) -> Any:
        if not stack:
            raise VMError("Operand stack underflow.")

        return stack.pop()

    @classmethod
    def _pop_arguments(
        cls,
        stack: list[Any],
        count: int,
    ) -> list[Any]:
        if count < 0:
            raise VMError(
                "Argument count cannot be negative."
            )

        if len(stack) < count:
            raise VMError(
                "Operand stack underflow while reading "
                "function arguments."
            )

        if count == 0:
            return []

        arguments = stack[-count:]
        del stack[-count:]

        return arguments

    # ------------------------------------------------------------------
    # Operand validation
    # ------------------------------------------------------------------

    @staticmethod
    def _require_operand(
        operand: object | None,
        message: str,
    ) -> Any:
        if operand is None:
            raise VMError(message)

        return operand

    @staticmethod
    def _require_jump_target(
        operand: object | None,
    ) -> int:
        if operand is None:
            raise VMError(
                "Jump instruction requires a target."
            )

        if isinstance(operand, bool):
            raise VMError(
                "Jump target must be an integer instruction index."
            )

        if not isinstance(operand, int):
            raise VMError(
                "Jump target must be an integer instruction index."
            )

        if operand < 0:
            raise VMError(
                "Jump target cannot be negative."
            )

        return operand

    # ------------------------------------------------------------------
    # Agent call resolution
    # ------------------------------------------------------------------

    def _resolve_agent_call(
        self,
        current_agent: Any,
        target: Any,
    ) -> tuple[Any, str]:
        """
        Resolve CALL_AGENT operands.

        Supported forms:

            "function"
                Call a function on the current agent.

            ("agent_name", "function")
                Call a function on another agent.

        This preserves the compact IR representation while allowing
        cross-agent invocation.
        """
        if isinstance(target, tuple):
            if len(target) != 2:
                raise VMError(
                    "CALL_AGENT tuple operand must contain "
                    "(agent_name, function_name)."
                )

            agent_name, function_name = target

            if not isinstance(agent_name, str):
                raise VMError(
                    "CALL_AGENT agent name must be a string."
                )

            if not isinstance(function_name, str):
                raise VMError(
                    "CALL_AGENT function name must be a string."
                )

            target_agent = self.vm.get_agent(agent_name)

            if target_agent is None:
                raise VMError(
                    f"Agent '{agent_name}' not found."
                )

            return target_agent, function_name

        if isinstance(target, str):
            return current_agent, target

        raise VMError(
            "CALL_AGENT operand must be a function name or "
            "(agent_name, function_name) tuple."
        )

    # ------------------------------------------------------------------
    # Primitive operations
    # ------------------------------------------------------------------

    @staticmethod
    def binary(
        opcode: OpCode,
        left: Any,
        right: Any,
    ) -> Any:
        if opcode == OpCode.ADD:
            return left + right

        if opcode == OpCode.SUB:
            return left - right

        if opcode == OpCode.MUL:
            return left * right

        if opcode == OpCode.DIV:
            if right == 0:
                raise VMError("Division by zero.")

            return left / right

        if opcode == OpCode.MOD:
            if right == 0:
                raise VMError("Modulo by zero.")

            return left % right

        if opcode == OpCode.EQUAL:
            return left == right

        if opcode == OpCode.NOT_EQUAL:
            return left != right

        if opcode == OpCode.LESS:
            return left < right

        if opcode == OpCode.LESS_EQUAL:
            return left <= right

        if opcode == OpCode.GREATER:
            return left > right

        if opcode == OpCode.GREATER_EQUAL:
            return left >= right

        if opcode == OpCode.AND:
            return bool(left) and bool(right)

        if opcode == OpCode.OR:
            return bool(left) or bool(right)

        raise VMError(
            f"Unsupported binary opcode: {opcode!r}"
        )


__all__ = [
    "ExecutionEngine",
        ]
