from __future__ import annotations

from compiler.ir import IRFunction, IRModule

from .errors import VMError
from .frame import CallFrame


class CallExecutor:
    """Handles CARDINAL function and agent-function calls."""

    def __init__(self, vm) -> None:
        self.vm = vm

    def call(
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
                f"Unknown function: {function_name}"
            )

        return self.invoke_function(
            target,
            module,
            caller_frame,
        )

    def call_agent(
        self,
        instruction,
        module: IRModule | None,
        caller_frame: CallFrame,
    ) -> object | None:
        if self.vm.current_agent is None:
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

        target = self.vm.current_agent.get_function(
            function_name
        )

        if target is None:
            raise VMError(
                f"Unknown agent function: "
                f"{self.vm.current_agent.name}."
                f"{function_name}"
            )

        result = self.invoke_function(
            target,
            module,
            caller_frame,
        )

        for name, value in (
            self.vm.current_agent.state.items()
        ):
            if name in caller_frame.locals:
                caller_frame.locals[name] = value

        return result

    def invoke_function(
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

        if self.vm.current_agent is not None:
            for name, value in (
                self.vm.current_agent.state.items()
            ):
                function_locals.setdefault(
                    name,
                    value,
                )

        frame = CallFrame(
            function_name=target.name,
            locals=function_locals,
        )

        self.vm.frames.append(frame)

        result = self.vm.execution.execute_function(
            target,
            module,
            frame,
        )

        if self.vm.current_agent is not None:
            for name in self.vm.current_agent.state:
                if name in frame.locals:
                    self.vm.current_agent.state[name] = (
                        frame.locals[name]
                    )

        if (
            self.vm.frames
            and self.vm.frames[-1] is frame
        ):
            self.vm.frames.pop()

        return result
