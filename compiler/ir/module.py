from __future__ import annotations

from dataclasses import dataclass, field

from .instructions import Instruction


@dataclass
class IRFunction:
    name: str
    parameters: list[str] = field(default_factory=list)
    instructions: list[Instruction] = field(default_factory=list)

    def emit(self, instruction: Instruction) -> None:
        self.instructions.append(instruction)


@dataclass
class IRModule:
    name: str = "main"
    functions: list[IRFunction] = field(default_factory=list)

    def add_function(self, function: IRFunction) -> None:
        self.functions.append(function)
