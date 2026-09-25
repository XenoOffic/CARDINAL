from __future__ import annotations

from typing import TYPE_CHECKING

from compiler.ir import (
    IRBehavior,
    IRFunction,
    IRInstruction,
    IRModule,
    OpCode,
)

from .errors import VMError
from .frame import CallFrame

if TYPE_CHECKING:
    from .vm import VM


class ExecutionEngine:
    """Executes CARDINAL IR instructions."""

    def __init__(self, vm: VM) -> None:
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
        instructions: list[IRInstruction],
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

            frame.instruction_pointer += 1

            self.consume_instruction()

            result = self.execute_instruction(
                instruction,
                module,
                frame,
            )

            if result is not _CONTINUE:
                return result

        return None

    def consume_instruction(self) -> None:
        self.vm.limits.consume()

        self.vm._execution_instruction_count += 1

        agent = self.vm.current_agent

        if agent is not None:
            agent.context.instructions_executed += 1

    def execute_instruction(
        self,
        instruction: IRInstruction,
        module: IRModule | None,
        frame: CallFrame,
    ) -> object:
        opcode = instruction.opcode
        operand = instruction.operand

        if opcode == OpCode.CONSTANT:
            frame.operand_stack.append(operand)
            return _CONTINUE

        if opcode == OpCode.LOAD:
            frame.operand_stack.append(
                frame.lookup(str(operand))
            )
            return _CONTINUE

        if opcode == OpCode.STORE:
            value = frame.operand_stack.pop()

            frame.declare(
                str(operand),
                value,
            )

            return _CONTINUE

        if opcode == OpCode.ASSIGN:
            value = frame.operand_stack.pop()

            frame.assign(
                str(operand),
                value,
            )

            return _CONTINUE

        if opcode == OpCode.ENTER_SCOPE:
            frame.enter_scope()
            return _CONTINUE

        if opcode == OpCode.EXIT_SCOPE:
            frame.exit_scope()
            return _CONTINUE

        if opcode == OpCode.ADD:
            self.binary("+", frame)
            return _CONTINUE

        if opcode == OpCode.SUB:
            self.binary("-", frame)
            return _CONTINUE

        if opcode == OpCode.MUL:
            self.binary("*", frame)
            return _CONTINUE

        if opcode == OpCode.DIV:
            self.binary("/", frame)
            return _CONTINUE

        if opcode == OpCode.MOD:
            self.binary("%", frame)
            return _CONTINUE

        if opcode == OpCode.NEGATE:
            value = frame.operand_stack.pop()
            frame.operand_stack.append(-value)
            return _CONTINUE

        if opcode == OpCode.NOT:
            value = frame.operand_stack.pop()
            frame.operand_stack.append(not value)
            return _CONTINUE

        if opcode == OpCode.EQUAL:
            self.binary("==", frame)
            return _CONTINUE

        if opcode == OpCode.NOT_EQUAL:
            self.binary("!=", frame)
            return _CONTINUE

        if opcode == OpCode.LESS:
            self.binary("<", frame)
            return _CONTINUE

        if opcode == OpCode.LESS_EQUAL:
            self.binary("<=", frame)
            return _CONTINUE

        if opcode == OpCode.GREATER:
            self.binary(">", frame)
            return _CONTINUE

        if opcode == OpCode.GREATER_EQUAL:
            self.binary(">=", frame)
            return _CONTINUE

        if opcode == OpCode.AND:
            self.binary("and", frame)
            return _CONTINUE

        if opcode == OpCode.OR:
            self.binary("or", frame)
            return _CONTINUE

        if opcode == OpCode.CALL:
            return self.vm.calls.call(
                operand,
                module,
                frame,
            )

        if opcode == OpCode.CALL_AGENT:
            return self.vm.calls.call_agent(
                operand,
                module,
                frame,
            )

        if opcode == OpCode.JUMP:
            frame.instruction_pointer = int(
                operand
            )
            return _CONTINUE

        if opcode == OpCode.JUMP_IF_FALSE:
            condition = frame.operand_stack.pop()

            if not condition:
                frame.instruction_pointer = int(
                    operand
                )

            return _CONTINUE

        if opcode == OpCode.RETURN:
            if frame.operand_stack:
                return frame.operand_stack.pop()

            return None

        if opcode == OpCode.HALT:
            return frame.operand_stack[-1] if (
                frame.operand_stack
            ) else None

        raise VMError(
            f"Unsupported opcode: {opcode}"
        )

    def binary(
        self,
        operator: str,
        frame: CallFrame,
    ) -> None:
        right = frame.operand_stack.pop()
        left = frame.operand_stack.pop()

        if operator == "+":
            result = left + right
        elif operator == "-":
            result = left - right
        elif operator == "*":
            result = left * right
        elif operator == "/":
            result = left / right
        elif operator == "%":
            result = left % right
        elif operator == "==":
            result = left == right
        elif operator == "!=":
            result = left != right
        elif operator == "<":
            result = left < right
        elif operator == "<=":
            result = left <= right
        elif operator == ">":
            result = left > right
        elif operator == ">=":
            result = left >= right
        elif operator == "and":
            result = bool(left and right)
        elif operator == "or":
            result = bool(left or right)
        else:
            raise VMError(
                f"Unsupported binary operator: "
                f"{operator}"
            )

        frame.operand_stack.append(result)


_CONTINUE = object()


__all__ = [
    "ExecutionEngine",
        ]
