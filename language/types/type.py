from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TypeKind(Enum):
    INT = "Int"
    FLOAT = "Float"
    BOOL = "Bool"
    STRING = "String"
    UNIT = "Unit"
    ANY = "Any"
    AGENT = "Agent"
    FUNCTION = "Function"
    UNKNOWN = "Unknown"


@dataclass(frozen=True)
class CardinalType:
    kind: TypeKind
    name: str | None = None

    def __str__(self) -> str:
        return self.name or self.kind.value


INT = CardinalType(TypeKind.INT)
FLOAT = CardinalType(TypeKind.FLOAT)
BOOL = CardinalType(TypeKind.BOOL)
STRING = CardinalType(TypeKind.STRING)
UNIT = CardinalType(TypeKind.UNIT)
ANY = CardinalType(TypeKind.ANY)
UNKNOWN = CardinalType(TypeKind.UNKNOWN)
