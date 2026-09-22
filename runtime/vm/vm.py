from __future__ import annotations

from compiler.ir import IRFunction, IRModule, OpCode

from .frame import CallFrame


class VMError(Exception):
    """Raised when the CARDINAL VM encounters an execution error."""


class VM:
    """Stack-based virtual machine for CARDINAL IR."""

    def __init__(self) -> None:
        self.frames: list[CallFrame] = []
        self.return_value: object | None = None

    def execute(
        self,
        function: IRFunction,
        module: IRModule | None = None,
    ) -> object | None:
        self.frames.clear()
        self.return_value = None

        frame = CallFrame(function_name=function.name)
        self.frames.append(frame)

        result = self._execute_function(
            function,
            module,
            frame,
        )

        self.return_value = result
        self.frames.clear()

        return result

    def _execute_function(
        self,
        function: IRFunction,
        module: IRModule | None,
        frame: CallFrame,
    ) -> object | None:
        instructions = function.instructions

        while frame.instruction_pointer < len(instructions):
            instruction = instructions[frame.instruction_pointer]
            opcode = instruction.opcode
            stack = frame.operand_stack

            if opcode == OpCode.CONSTANT:
                stack.append(instruction.operand)

            elif opcode == OpCode.LOAD:
                name = instruction.operand

                if not isinstance(name, str):
                    raise VMError("LOAD requires a variable name")

                if name not in frame.locals:
                    raise VMError(
                        f"Undefined variable: {name}"
                    )

                stack.append(frame.locals[name])

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

                frame.locals[name] = stack.pop()

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

                frame.locals[name] = stack.pop()

            elif opcode == OpCode.ADD:
                self._binary(frame, lambda a, b: a + b)

            elif opcode == OpCode.SUB:
                self._binary(frame, lambda a, b: a - b)

            elif opcode == OpCode.MUL:
                self._binary(frame, lambda a, b: a * b)

            elif opcode == OpCode.DIV:
                self._binary(frame, lambda a, b: a / b)

            elif opcode == OpCode.MOD:
                self._binary(frame, lambda a, b: a % b)

            elif opcode == OpCode.EQUAL:
                self._binary(frame, lambda a, b: a == b)

            elif opcode == OpCode.NOT_EQUAL:
                self._binary(frame, lambda a, b: a != b)

            elif opcode == OpCode.LESS:
                self._binary(frame, lambda a, b: a < b)

            elif opcode == OpCode.LESS_EQUAL:
                self._binary(frame, lambda a, b: a <= b)

            elif opcode == OpCode.GREATER:
                self._binary(frame, lambda a, b: a > b)

            elif opcode == OpCode.GREATER_EQUAL:
                self._binary(frame, lambda a, b: a >= b)

            elif opcode == OpCode.CALL:
                result = self._call(
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
                result = stack.pop() if stack else None
                frame.return_value = result

                if self.frames and self.frames[-1] is frame:
                    self.frames.pop()

                return result

            elif opcode == OpCode.HALT:
                return None

            else:
                raise VMError(
                    f"Unsupported opcode: {opcode.name}"
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

        if not isinstance(function_name, str):
            raise VMError(
                "CALL requires a function name"
            )

        target = next(
            (
                function
                for function in module.functions
                if function.name == function_name
            ),
            None,
        )

        if target is None:
            raise VMError(
                f"Unknown function: {function_name}"
            )

        argument_count = len(target.parameters)

        if len(caller_frame.operand_stack) < argument_count:
            raise VMError(
                f"Not enough arguments for "
                f"function '{function_name}'"
            )

        if argument_count == 0:
            arguments = []
        else:
            arguments = caller_frame.operand_stack[
                -argument_count:
            ]

            del caller_frame.operand_stack[
                -argument_count:
            ]

        frame = CallFrame(
            function_name=function_name,
            locals=dict(
                zip(
                    target.parameters,
                    arguments,
                )
            ),
        )

        self.frames.append(frame)

        return self._execute_function(
            target,
            module,
            frame,
        )

    def _binary(
        self,
        frame: CallFrame,
        operation,
    ) -> None:
        stack = frame.operand_stack

        if len(stack) < 2:
            raise VMError(
                "Stack underflow during binary operation"
            )

        right = stack.pop()
        left = stack.pop()

        try:
            result = operation(left, right)
        except Exception as exc:
            raise VMError(
                f"Binary operation failed: {exc}"
            ) from exc

        stack.append(result)
