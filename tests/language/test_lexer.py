from language.lexer.lexer import Lexer
from language.lexer.token import TokenType


def test_hello_agent():
    source = """
    agent HelloAgent {
        behavior greet {
            let message: String = "Hello, CARDINAL";
            return;
        }
    }
    """

    tokens = Lexer(source).tokenize()

    token_types = [token.type for token in tokens]

    assert token_types == [
        TokenType.AGENT,
        TokenType.IDENTIFIER,
        TokenType.LBRACE,

        TokenType.BEHAVIOR,
        TokenType.IDENTIFIER,
        TokenType.LBRACE,

        TokenType.LET,
        TokenType.IDENTIFIER,
        TokenType.COLON,
        TokenType.STRING_TYPE,
        TokenType.ASSIGN,
        TokenType.STRING,
        TokenType.SEMICOLON,

        TokenType.RETURN,
        TokenType.SEMICOLON,

        TokenType.RBRACE,
        TokenType.RBRACE,

        TokenType.EOF,
    ]
