from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class OpCode(Enum):
    CONSTANT = auto()
    LOAD = auto()
    STORE = auto()
    ASSIGN = auto()

    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()

    NEGATE = auto()
    NOT = auto()

    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()

    AND = auto()
    OR = auto()

    CALL = auto()
    RETURN = auto()

    JUMP = auto()
    JUMP_IF_FALSE = auto()

    HALT = auto()


@dataclass(frozen=True)
class Instruction:
    opcode: OpCode
    operand: object | None = None

    def __str__(self) -> str:
        if self.operand is None:
            return self.opcode.name

        return f"{self.opcode.name} {self.operand}"
