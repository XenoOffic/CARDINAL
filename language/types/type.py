from __future__ import annotations

from dataclasses import dataclass, field
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
    parameters: tuple[CardinalType, ...] = field(
        default_factory=tuple
    )
    return_type: CardinalType | None = None

    def __str__(self) -> str:
        if self.kind == TypeKind.FUNCTION:
            parameters = ", ".join(
                str(parameter)
                for parameter in self.parameters
            )

            result = (
                str(self.return_type)
                if self.return_type is not None
                else "Unit"
            )

            return f"Function({parameters}) -> {result}"

        return self.name or self.kind.value


INT = CardinalType(TypeKind.INT)
FLOAT = CardinalType(TypeKind.FLOAT)
BOOL = CardinalType(TypeKind.BOOL)
STRING = CardinalType(TypeKind.STRING)
UNIT = CardinalType(TypeKind.UNIT)
ANY = CardinalType(TypeKind.ANY)
UNKNOWN = CardinalType(TypeKind.UNKNOWN)


def function_type(
    parameters: list[CardinalType] | tuple[CardinalType, ...],
    return_type: CardinalType,
) -> CardinalType:
    return CardinalType(
        kind=TypeKind.FUNCTION,
        parameters=tuple(parameters),
        return_type=return_type,
            )
