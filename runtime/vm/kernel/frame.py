from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CallFrame:
    """Execution frame used by the CARDINAL virtual machine."""

    function_name: str
    instruction_pointer: int = 0

    locals: dict[str, object] = field(
        default_factory=dict
    )

    operand_stack: list[object] = field(
        default_factory=list
    )

    return_value: object | None = None

    scopes: list[dict[str, object]] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        if not self.scopes:
            self.scopes.append(self.locals)

    def enter_scope(self) -> None:
        self.scopes.append({})

    def exit_scope(self) -> None:
        if len(self.scopes) <= 1:
            raise RuntimeError(
                "Cannot exit the root scope."
            )

        self.scopes.pop()

    def declare(
        self,
        name: str,
        value: object,
    ) -> None:
        self.scopes[-1][name] = value

    def lookup(
        self,
        name: str,
    ) -> object:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        raise KeyError(name)

    def assign(
        self,
        name: str,
        value: object,
    ) -> None:
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name] = value
                return

        self.scopes[-1][name] = value
