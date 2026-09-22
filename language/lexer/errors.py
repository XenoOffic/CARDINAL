class LexerError(Exception):
    """Raised when CARDINAL source cannot be tokenized."""

    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column

        super().__init__(
            f"{line}:{column}: lexer error: {message}"
        )
