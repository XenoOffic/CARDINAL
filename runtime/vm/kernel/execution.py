from __future__ import annotations

from typing import Callable

from compiler.ir import IRBehavior, IRFunction, IRModule, OpCode

from .errors import VMError
from .frame import CallFrame


class ExecutionEngine:
    """Executes CARDINAL IR instructions."""

    def __init__(self, vm) -> None:
        self.vm = vm

    def execute_function(
        self,
        function: IRFunction,
        module: IRModule | None,
        frame: CallFrame,
    ) -> object | None:
        return self.execute_instructions(
            function.instructions,
            module,
            frame,
        )

    def execute_behavior(
        self,
        behavior: IRBehavior,
        module: IRModule | None,
        frame: CallFrame,
    ) -> object | None:
        return self.execute_instructions(
            behavior.instructions,
            module,
            frame,
        )

    def execute_instructions(
        self,
        instructions,
        module: IRModule | None,
        frame: CallFrame,
    ) -> object | None:
        while (
            frame.instruction_pointer
            < len(instructions)
        ):
            self.vm.limits.consume()

            instruction = instructions[
                frame.instruction_pointer
            ]

            opcode = instruction.opcode
            stack = frame.operand_stack

            if opcode == OpCode.CONSTANT:
                stack.append(instruction.operand)

            elif opcode == OpCode.LOAD:
                self._load(
                    frame,
                    instruction.operand,
                )

            elif opcode == OpCode.STORE:
                self._store(
                    frame,
                    instruction.operand,
                )

            elif opcode == OpCode.ASSIGN:
                self._assign(
                    frame,
                    instruction.operand,
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
                self._negate(frame)

            elif opcode == OpCode.NOT:
                self._not(frame)

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
                result = self.vm.calls.call(
                    instruction,
                    module,
                    frame,
                )

                if result is not None:
                    stack.append(result)

            elif opcode == OpCode.CALL_AGENT:
                result = self.vm.calls.call_agent(
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
                        "Stack underflow during JUMP_IF_FALSE"
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
                    self.vm.frames
                    and self.vm.frames[-1] is frame
                ):
                    self.vm.frames.pop()

                return result

            elif opcode == OpCode.HALT:
                return None

            else:
                raise VMError(
                    f"Unsupported opcode: {opcode.name}"
                )

            frame.instruction_pointer += 1

        return frame.return_value

    def _load(
        self,
        frame: CallFrame,
        operand,
    ) -> None:
        name = operand

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

        frame.operand_stack.append(value)

    def _store(
        self,
        frame: CallFrame,
        operand,
    ) -> None:
        if not frame.operand_stack:
            raise VMError(
                "Stack underflow during STORE"
            )

        name = operand

        if not isinstance(name, str):
            raise VMError(
                "STORE requires a variable name"
            )

        frame.declare(
            name,
            frame.operand_stack.pop(),
        )

    def _assign(
        self,
        frame: CallFrame,
        operand,
    ) -> None:
        if not frame.operand_stack:
            raise VMError(
                "Stack underflow during ASSIGN"
            )

        name = operand

        if not isinstance(name, str):
            raise VMError(
                "ASSIGN requires a variable name"
            )

        value = frame.operand_stack.pop()

        frame.assign(
            name,
            value,
        )

    def _negate(
        self,
        frame: CallFrame,
    ) -> None:
        if not frame.operand_stack:
            raise VMError(
                "Stack underflow during NEGATE"
            )

        value = frame.operand_stack.pop()

        try:
            frame.operand_stack.append(-value)
        except Exception as exc:
            raise VMError(
                f"Unary negation failed: {exc}"
            ) from exc

    def _not(
        self,
        frame: CallFrame,
    ) -> None:
        if not frame.operand_stack:
            raise VMError(
                "Stack underflow during NOT"
            )

        value = frame.operand_stack.pop()

        frame.operand_stack.append(
            not value
        )

    def _binary(
        self,
        frame: CallFrame,
        operation: Callable[
            [object, object],
            object,
        ],
    ) -> None:
        stack = frame.operand_stack

        if len(stack) < 2:
            raise VMError(
                "Stack underflow during binary operation"
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
