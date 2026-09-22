from __future__ import annotations

from compiler.ir import IRFunction, IRModule, OpCode


class VMError(Exception):
    """Raised when the CARDINAL VM encounters an execution error."""


class VM:
    """Stack-based virtual machine for CARDINAL IR."""

    def __init__(self) -> None:
        self.stack: list[object] = []
        self.variables: dict[str, object] = {}
        self.return_value: object | None = None

    def execute(
        self,
        function: IRFunction,
        module: IRModule | None = None,
    ) -> object | None:
        self.stack.clear()
        self.variables.clear()
        self.return_value = None

        return self._execute_function(function, module)

    def _execute_function(
        self,
        function: IRFunction,
        module: IRModule | None,
    ) -> object | None:
        instructions = function.instructions
        instruction_pointer = 0

        while instruction_pointer < len(instructions):
            instruction = instructions[instruction_pointer]
            opcode = instruction.opcode

            if opcode == OpCode.CONSTANT:
                self.stack.append(instruction.operand)

            elif opcode == OpCode.LOAD:
                name = instruction.operand

                if name not in self.variables:
                    raise VMError(
                        f"Undefined variable: {name}"
                    )

                self.stack.append(self.variables[name])

            elif opcode == OpCode.STORE:
                if not self.stack:
                    raise VMError(
                        "Stack underflow during STORE"
                    )

                name = instruction.operand
                self.variables[name] = self.stack.pop()

            elif opcode == OpCode.ADD:
                self._binary(lambda a, b: a + b)

            elif opcode == OpCode.SUB:
                self._binary(lambda a, b: a - b)

            elif opcode == OpCode.MUL:
                self._binary(lambda a, b: a * b)

            elif opcode == OpCode.DIV:
                self._binary(lambda a, b: a / b)

            elif opcode == OpCode.MOD:
                self._binary(lambda a, b: a % b)

            elif opcode == OpCode.EQUAL:
                self._binary(lambda a, b: a == b)

            elif opcode == OpCode.NOT_EQUAL:
                self._binary(lambda a, b: a != b)

            elif opcode == OpCode.LESS:
                self._binary(lambda a, b: a < b)

            elif opcode == OpCode.LESS_EQUAL:
                self._binary(lambda a, b: a <= b)

            elif opcode == OpCode.GREATER:
                self._binary(lambda a, b: a > b)

            elif opcode == OpCode.GREATER_EQUAL:
                self._binary(lambda a, b: a >= b)

            elif opcode == OpCode.CALL:
                if module is None:
                    raise VMError(
                        "CALL requires an IR module."
                    )

                function_name = instruction.operand

                target = next(
                    (
                        item
                        for item in module.functions
                        if item.name == function_name
                    ),
                    None,
                )

                if target is None:
                    raise VMError(
                        f"Unknown function: {function_name}"
                    )

                argument_count = len(target.parameters)

                if len(self.stack) < argument_count:
                    raise VMError(
                        f"Not enough arguments for "
                        f"function '{function_name}'"
                    )

                arguments = self.stack[
                    -argument_count:
                ]

                del self.stack[-argument_count:]

                previous_variables = self.variables
                self.variables = dict(
                    zip(target.parameters, arguments)
                )

                result = self._execute_function(
                    target,
                    module,
                )

                self.variables = previous_variables

                if result is not None:
                    self.stack.append(result)

            elif opcode == OpCode.RETURN:
                self.return_value = (
                    self.stack.pop()
                    if self.stack
                    else None
                )

                return self.return_value

            elif opcode == OpCode.HALT:
                return self.return_value

            else:
                raise VMError(
                    f"Unsupported opcode: {opcode.name}"
                )

            instruction_pointer += 1

        return self.return_value

    def _binary(self, operation) -> None:
        if len(self.stack) < 2:
            raise VMError(
                "Stack underflow during binary operation"
            )

        right = self.stack.pop()
        left = self.stack.pop()

        try:
            result = operation(left, right)
        except Exception as exc:
            raise VMError(
                f"Binary operation failed: {exc}"
            ) from exc

        self.stack.append(result)
