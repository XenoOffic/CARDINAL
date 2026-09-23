from __future__ import annotations

from language.ast import (
    AgentDeclaration,
    AssignmentExpression,
    BehaviorDeclaration,
    BinaryExpression,
    FunctionCall,
    FunctionDeclaration,
    Identifier,
    IfStatement,
    Literal,
    Program,
    ReturnStatement,
    UnaryExpression,
    VariableDeclaration,
    WhileStatement,
)
from language.lexer import Lexer, Token, TokenType


class Parser:
    """
    Recursive-descent parser for CARDINAL.

    Converts a stream of Lexer tokens into an AST.
    """

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    @classmethod
    def from_source(cls, source: str) -> "Parser":
        return cls(Lexer(source).tokenize())

    def parse(self) -> Program:
        declarations = []

        while not self._is_at_end():
            declarations.append(self._declaration())

        return Program(declarations)

    # ---------------------------------------------------------
    # Declarations
    # ---------------------------------------------------------

    def _declaration(self):
        if self._match(TokenType.AGENT):
            return self._agent_declaration()

        if self._match(TokenType.FN):
            return self._function_declaration()

        if self._match(TokenType.LET):
            return self._variable_declaration(False)

        if self._match(TokenType.CONST):
            self._consume(
                TokenType.LET,
                "Expected 'let' after 'const'.",
            )
            return self._variable_declaration(True)

        if self._match(TokenType.WHILE):
            return self._while_statement()

        if self._match(TokenType.IF):
            return self._if_statement()

        raise self._error(
            self._peek(),
            "Expected declaration.",
        )

    def _agent_declaration(self) -> AgentDeclaration:
        name = self._consume(
            TokenType.IDENTIFIER,
            "Expected agent name.",
        )

        parent = None

        if self._match(TokenType.COLON):
            parent = self._consume(
                TokenType.IDENTIFIER,
                "Expected parent agent name.",
            ).lexeme

        self._consume(
            TokenType.LBRACE,
            "Expected '{' after agent declaration.",
        )

        members = []

        while (
            not self._check(TokenType.RBRACE)
            and not self._is_at_end()
        ):
            if self._match(TokenType.BEHAVIOR):
                members.append(self._behavior_declaration())

            elif self._match(TokenType.FN):
                members.append(self._function_declaration())

            elif self._match(TokenType.LET):
                members.append(
                    self._variable_declaration(False)
                )

            elif self._match(TokenType.CONST):
                self._consume(
                    TokenType.LET,
                    "Expected 'let' after 'const'.",
                )
                members.append(
                    self._variable_declaration(True)
                )

            else:
                raise self._error(
                    self._peek(),
                    "Expected agent member.",
                )

        self._consume(
            TokenType.RBRACE,
            "Expected '}' after agent declaration.",
        )

        return AgentDeclaration(
            name=name.lexeme,
            parent=parent,
            members=members,
        )

    def _behavior_declaration(self) -> BehaviorDeclaration:
        name = self._consume(
            TokenType.IDENTIFIER,
            "Expected behavior name.",
        )

        body = self._block()

        return BehaviorDeclaration(
            name=name.lexeme,
            body=body,
        )

    def _function_declaration(self) -> FunctionDeclaration:
        name = self._consume(
            TokenType.IDENTIFIER,
            "Expected function name.",
        )

        self._consume(
            TokenType.LPAREN,
            "Expected '(' after function name.",
        )

        parameters = []

        if not self._check(TokenType.RPAREN):
            parameters.append(self._parameter())

            while self._match(TokenType.COMMA):
                parameters.append(self._parameter())

        self._consume(
            TokenType.RPAREN,
            "Expected ')' after parameters.",
        )

        return_type = None

        if self._match(TokenType.ARROW):
            return_type = self._type_name()

        body = self._block()

        return FunctionDeclaration(
            name=name.lexeme,
            parameters=parameters,
            return_type=return_type,
            body=body,
        )

    def _parameter(self) -> Identifier:
        name = self._consume(
            TokenType.IDENTIFIER,
            "Expected parameter name.",
        )

        self._consume(
            TokenType.COLON,
            "Expected ':' after parameter name.",
        )

        type_name = self._type_name()

        return Identifier(
            name=name.lexeme,
            type_name=type_name,
        )

    def _variable_declaration(
        self,
        constant: bool,
    ) -> VariableDeclaration:
        name = self._consume(
            TokenType.IDENTIFIER,
            "Expected variable name.",
        )

        type_name = None

        if self._match(TokenType.COLON):
            type_name = self._type_name()

        value = None

        if self._match(TokenType.ASSIGN):
            value = self._expression()

        self._consume(
            TokenType.SEMICOLON,
            "Expected ';' after variable declaration.",
        )

        return VariableDeclaration(
            name=name.lexeme,
            type_name=type_name,
            value=value,
            constant=constant,
        )

    # ---------------------------------------------------------
    # Statements
    # ---------------------------------------------------------

    def _statement(self):
        if self._match(TokenType.LET):
            return self._variable_declaration(False)

        if self._match(TokenType.CONST):
            self._consume(
                TokenType.LET,
                "Expected 'let' after 'const'.",
            )
            return self._variable_declaration(True)

        if self._match(TokenType.RETURN):
            value = None

            if not self._check(TokenType.SEMICOLON):
                value = self._expression()

            self._consume(
                TokenType.SEMICOLON,
                "Expected ';' after return statement.",
            )

            return ReturnStatement(value)

        if self._match(TokenType.IF):
            return self._if_statement()

        if self._match(TokenType.WHILE):
            return self._while_statement()

        if self._check(TokenType.LBRACE):
            return self._block()

        expression = self._expression()

        self._consume(
            TokenType.SEMICOLON,
            "Expected ';' after expression.",
        )

        return expression

    def _block(self) -> list:
        self._consume(
            TokenType.LBRACE,
            "Expected '{'.",
        )

        statements = []

        while (
            not self._check(TokenType.RBRACE)
            and not self._is_at_end()
        ):
            statements.append(self._statement())

        self._consume(
            TokenType.RBRACE,
            "Expected '}' after block.",
        )

        return statements

    def _if_statement(self) -> IfStatement:
        condition = self._expression()

        then_body = self._block()

        else_body = []

        if self._match(TokenType.ELSE):
            else_body = self._block()

        return IfStatement(
            condition=condition,
            then_body=then_body,
            else_body=else_body,
        )

    def _while_statement(self) -> WhileStatement:
        condition = self._expression()

        body = self._block()

        return WhileStatement(
            condition=condition,
            body=body,
        )

    # ---------------------------------------------------------
    # Expressions
    # ---------------------------------------------------------

    def _expression(self):
        return self._assignment()

    def _assignment(self):
        expression = self._logical_or()

        if self._match(
            TokenType.ASSIGN,
            TokenType.PLUS_ASSIGN,
            TokenType.MINUS_ASSIGN,
            TokenType.STAR_ASSIGN,
            TokenType.SLASH_ASSIGN,
        ):
            operator = self._previous().lexeme
            value = self._assignment()

            if not isinstance(expression, Identifier):
                raise self._error(
                    self._previous(),
                    "Invalid assignment target.",
                )

            return AssignmentExpression(
                target=expression.name,
                operator=operator,
                value=value,
            )

        return expression

    def _logical_or(self):
        expression = self._logical_and()

        while self._match(TokenType.OR):
            operator = self._previous().lexeme
            right = self._logical_and()

            expression = BinaryExpression(
                expression,
                operator,
                right,
            )

        return expression

    def _logical_and(self):
        expression = self._equality()

        while self._match(TokenType.AND):
            operator = self._previous().lexeme
            right = self._equality()

            expression = BinaryExpression(
                expression,
                operator,
                right,
            )

        return expression

    def _equality(self):
        expression = self._comparison()

        while self._match(
            TokenType.EQUAL,
            TokenType.NOT_EQUAL,
        ):
            operator = self._previous().lexeme
            right = self._comparison()

            expression = BinaryExpression(
                expression,
                operator,
                right,
            )

        return expression

    def _comparison(self):
        expression = self._term()

        while self._match(
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
        ):
            operator = self._previous().lexeme
            right = self._term()

            expression = BinaryExpression(
                expression,
                operator,
                right,
            )

        return expression

    def _term(self):
        expression = self._factor()

        while self._match(
            TokenType.PLUS,
            TokenType.MINUS,
        ):
            operator = self._previous().lexeme
            right = self._factor()

            expression = BinaryExpression(
                expression,
                operator,
                right,
            )

        return expression

    def _factor(self):
        expression = self._unary()

        while self._match(
            TokenType.STAR,
            TokenType.SLASH,
            TokenType.PERCENT,
        ):
            operator = self._previous().lexeme
            right = self._unary()

            expression = BinaryExpression(
                expression,
                operator,
                right,
            )

        return expression

    def _unary(self):
        if self._match(
            TokenType.NOT,
            TokenType.MINUS,
            TokenType.PLUS,
        ):
            operator = self._previous().lexeme
            operand = self._unary()

            return UnaryExpression(
                operator=operator,
                operand=operand,
            )

        return self._primary()

    def _primary(self):
        if self._match(TokenType.INTEGER):
            return Literal(int(self._previous().lexeme))

        if self._match(TokenType.FLOAT_LITERAL):
            return Literal(float(self._previous().lexeme))

        if self._match(TokenType.STRING):
            return Literal(self._previous().lexeme)

        if self._match(TokenType.TRUE):
            return Literal(True)

        if self._match(TokenType.FALSE):
            return Literal(False)

        if self._match(TokenType.NULL):
            return Literal(None)

        if self._match(TokenType.IDENTIFIER):
            identifier = self._previous()

            if self._match(TokenType.LPAREN):
                return self._finish_call(identifier)

            return Identifier(identifier.lexeme)

        if self._match(TokenType.LPAREN):
            expression = self._expression()

            self._consume(
                TokenType.RPAREN,
                "Expected ')' after expression.",
            )

            return expression

        raise self._error(
            self._peek(),
            "Expected expression.",
        )

    def _finish_call(self, name: Token) -> FunctionCall:
        arguments = []

        if not self._check(TokenType.RPAREN):
            arguments.append(self._expression())

            while self._match(TokenType.COMMA):
                arguments.append(self._expression())

        self._consume(
            TokenType.RPAREN,
            "Expected ')' after arguments.",
        )

        return FunctionCall(
            name=name.lexeme,
            arguments=arguments,
        )

    # ---------------------------------------------------------
    # Types
    # ---------------------------------------------------------

    def _type_name(self) -> str:
        valid_types = (
            TokenType.INT,
            TokenType.FLOAT,
            TokenType.BOOL,
            TokenType.STRING_TYPE,
            TokenType.UNIT,
            TokenType.ANY,
            TokenType.IDENTIFIER,
        )

        token = self._consume_any(
            valid_types,
            "Expected type.",
        )

        return token.lexeme

    # ---------------------------------------------------------
    # Token utilities
    # ---------------------------------------------------------

    def _match(self, *types: TokenType) -> bool:
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True

        return False

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return token_type == TokenType.EOF

        return self._peek().type == token_type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1

        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _consume(
        self,
        token_type: TokenType,
        message: str,
    ) -> Token:
        if self._check(token_type):
            return self._advance()

        raise self._error(
            self._peek(),
            message,
        )

    def _consume_any(
        self,
        token_types: tuple[TokenType, ...],
        message: str,
    ) -> Token:
        if self._peek().type in token_types:
            return self._advance()

        raise self._error(
            self._peek(),
            message,
        )

    def _error(self, token: Token, message: str):
        return SyntaxError(
            f"{message} "
            f"(line {token.line}, column {token.column})"
                )
