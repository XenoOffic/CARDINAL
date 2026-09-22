from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CallFrame:
    """Execution context for a CARDINAL function."""

    function_name: str
    instruction_pointer: int = 0
    locals: dict[str, object] = field(default_factory=dict)
    return_value: object | None = None
