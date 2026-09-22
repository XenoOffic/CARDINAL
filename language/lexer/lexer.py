from __future__ import annotations

from dataclasses import dataclass

from .token import Token, TokenType


KEYWORDS = {
    "agent": TokenType.AGENT,
    "behavior": TokenType.BEHAVIOR,
    "fn": TokenType.FN,
    "let": TokenType.LET,
    "const": TokenType.CONST,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "import": TokenType.IMPORT,

    "Int": TokenType.INT,
    "Float": TokenType.FLOAT,
    "Bool": TokenType.BOOL,
    "String": TokenType.STRING_TYPE,
    "Unit": TokenType.UNIT,
    "Any": TokenType.ANY,

    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
}


@dataclass
class Lexer:
    source: str

    def __post_init__(self) -> None:
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while not self._at_end():
            self._scan_token()

        self.tokens.append(
            Token(
                TokenType.EOF,
                "",
                self.line,
                self.column,
            )
        )

        return self.tokens

    def _scan_token(self) -> None:
        char = self._advance()

        if char in " \t\r":
            return

        if char == "\n":
            self.line += 1
            self.column = 1
            return

        if char == "/" and self._match("/"):
            self._skip_line_comment()
            return

        if char == "/" and self._match("*"):
            self._skip_block_comment()
            return

        if char.isalpha() or char == "_":
            self._identifier()
            return

        if char.isdigit():
            self._number()
            return

        if char == '"':
            self._string()
            return

        single_character_tokens = {
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            ",": TokenType.COMMA,
            ":": TokenType.COLON,
            ";": TokenType.SEMICOLON,
        }

        if char in single_character_tokens:
            self._add_token(single_character_tokens[char])
            return

        if char == ".":
            # Decimal numbers are handled by _number().
            self._error("Unexpected '.'")
            return

        if char == "=":
            if self._match("="):
                self._add_token(TokenType.EQUAL)
            else:
                self._add_token(TokenType.ASSIGN)
            return

        if char == "!":
            if self._match("="):
                self._add_token(TokenType.NOT_EQUAL)
            else:
                self._add_token(TokenType.NOT)
            return

        if char == "<":
            if self._match("="):
                self._add_token(TokenType.LESS_EQUAL)
            else:
                self._add_token(TokenType.LESS)
            return

        if char == ">":
            if self._match("="):
                self._add_token(TokenType.GREATER_EQUAL)
            else:
                self._add_token(TokenType.GREATER)
            return

        if char == "&":
            if self._match("&"):
                self._add_token(TokenType.AND)
            else:
                self._error("Expected '&' after '&'")
            return

        if char == "|":
            if self._match("|"):
                self._add_token(TokenType.OR)
            else:
                self._error("Expected '|' after '|'")
            return

        if char == "+":
            if self._match("="):
                self._add_token(TokenType.PLUS_ASSIGN)
            else:
                self._add_token(TokenType.PLUS)
            return

        if char == "-":
            if self._match("="):
                self._add_token(TokenType.MINUS_ASSIGN)
            elif self._match(">"):
                self._add_token(TokenType.ARROW)
            else:
                self._add_token(TokenType.MINUS)
            return

        if char == "*":
            if self._match("="):
                self._add_token(TokenType.STAR_ASSIGN)
            else:
                self._add_token(TokenType.STAR)
            return

        if char == "/":
            if self._match("="):
                self._add_token(TokenType.SLASH_ASSIGN)
            else:
                self._add_token(TokenType.SLASH)
            return

        self._error(f"Unexpected character {char!r}")

    def _identifier(self) -> None:
        start = self.position - 1

        while not self._at_end():
            char = self._peek()

            if char.isalnum() or char == "_":
                self._advance()
            else:
                break

        lexeme = self.source[start:self.position]
        token_type = KEYWORDS.get(lexeme, TokenType.IDENTIFIER)

        self._add_token(token_type, lexeme)

    def _number(self) -> None:
        start = self.position - 1

        while not self._at_end() and self._peek().isdigit():
            self._advance()

        token_type = TokenType.INTEGER

        if not self._at_end() and self._peek() == ".":
            self._advance()

            if self._at_end() or not self._peek().isdigit():
                self._error("Expected digit after decimal point")
                return

            while not self._at_end() and self._peek().isdigit():
                self._advance()

            token_type = TokenType.FLOAT_LITERAL

        lexeme = self.source[start:self.position]
        self._add_token(token_type, lexeme)

    def _string(self) -> None:
        start = self.position

        while not self._at_end() and self._peek() != '"':
            if self._peek() == "\n":
                self.line += 1
                self.column = 1

            self._advance()

        if self._at_end():
            self._error("Unterminated string")
            return

        self._advance()

        lexeme = self.source[start:self.position - 1]
        self._add_token(TokenType.STRING, lexeme)

    def _skip_line_comment(self) -> None:
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        while not self._at_end():
            if self._peek() == "*" and self._peek_next() == "/":
                self._advance()
                self._advance()
                return

            if self._peek() == "\n":
                self.line += 1
                self.column = 1

            self._advance()

        self._error("Unterminated block comment")

    def _advance(self) -> str:
        char = self.source[self.position]
        self.position += 1
        self.column += 1
        return char

    def _peek(self) -> str:
        if self._at_end():
            return "\0"

        return self.source[self.position]

    def _peek_next(self) -> str:
        if self.position + 1 >= len(self.source):
            return "\0"

        return self.source[self.position + 1]

    def _match(self, expected: str) -> bool:
        if self._at_end():
            return False

        if self.source[self.position] != expected:
            return False

        self.position += 1
        self.column += 1
        return True

    def _at_end(self) -> bool:
        return self.position >= len(self.source)

    def _add_token(
        self,
        token_type: TokenType,
        lexeme: str | None = None,
    ) -> None:
        if lexeme is None:
            lexeme = self.source[self.position - 1:self.position]

        self.tokens.append(
            Token(
                token_type,
                lexeme,
                self.line,
                self.column - len(lexeme),
            )
        )

    def _error(self, message: str) -> None:
        raise SyntaxError(
            f"Lexer error at line {self.line}, "
            f"column {self.column}: {message}"
  )
