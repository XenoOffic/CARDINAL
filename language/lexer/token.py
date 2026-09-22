from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    # Keywords
    AGENT = auto()
    BEHAVIOR = auto()
    FN = auto()
    LET = auto()
    CONST = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    IMPORT = auto()

    # Types
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    STRING_TYPE = auto()
    UNIT = auto()
    ANY = auto()

    # Literals
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT_LITERAL = auto()
    STRING = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()

    ASSIGN = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()
    STAR_ASSIGN = auto()
    SLASH_ASSIGN = auto()

    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()

    AND = auto()
    OR = auto()
    NOT = auto()

    # Symbols
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    COLON = auto()
    SEMICOLON = auto()
    ARROW = auto()
    DOUBLE_COLON = auto()

    # Special
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int

    def __repr__(self) -> str:
        return (
            f"Token("
            f"type={self.type.name}, "
            f"lexeme={self.lexeme!r}, "
            f"line={self.line}, "
            f"column={self.column}"
            f")"
      )
