from __future__ import annotations

from language.ast import (
    AgentDeclaration,
    BehaviorDeclaration,
    Identifier,
    Literal,
    Program,
    ReturnStatement,
    VariableDeclaration,
)
from language.types import (
    ANY,
    BOOL,
    FLOAT,
    INT,
    STRING,
    UNKNOWN,
    CardinalType,
)


class SemanticError(Exception):
    """Raised when CARDINAL code is semantically invalid."""


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.variables: dict[str, CardinalType] = {}
        self.agents: set[str] = set()
        self.errors: list[str] = []

    def analyze(self, program: Program) -> None:
        for declaration in program.declarations:
            self._declaration(declaration)

        if self.errors:
            raise SemanticError("\n".join(self.errors))

    def _declaration(self, node) -> None:
        if isinstance(node, AgentDeclaration):
            self._agent(node)
        elif isinstance(node, VariableDeclaration):
            self._variable(node)

    def _agent(self, node: AgentDeclaration) -> None:
        if node.name in self.agents:
            self._error(f"Agent '{node.name}' is already declared.")
            return

        self.agents.add(node.name)

        previous_variables = self.variables
        self.variables = {}

        for member in node.members:
            if isinstance(member, BehaviorDeclaration):
                for statement in member.body:
                    self._statement(statement)
            elif isinstance(member, VariableDeclaration):
                self._variable(member)

        self.variables = previous_variables

    def _variable(self, node: VariableDeclaration) -> None:
        if node.name in self.variables:
            self._error(
                f"Variable '{node.name}' is already declared."
            )
            return

        value_type = UNKNOWN

        if node.value is not None:
            value_type = self._expression_type(node.value)

        if node.type_name is not None:
            declared_type = self._resolve_type(node.type_name)

            if not self._compatible(declared_type, value_type):
                self._error(
                    f"Cannot assign {value_type} to "
                    f"variable '{node.name}' of type {declared_type}."
                )

            value_type = declared_type

        self.variables[node.name] = value_type

    def _statement(self, node) -> None:
        if isinstance(node, VariableDeclaration):
            self._variable(node)
        elif isinstance(node, ReturnStatement):
            if node.value is not None:
                self._expression_type(node.value)

    def _expression_type(self, node) -> CardinalType:
        if isinstance(node, Literal):
            if isinstance(node.value, bool):
                return BOOL

            if isinstance(node.value, int):
                return INT

            if isinstance(node.value, float):
                return FLOAT

            if isinstance(node.value, str):
                return STRING

            if node.value is None:
                return UNKNOWN

        if isinstance(node, Identifier):
            if node.name not in self.variables:
                self._error(
                    f"Unknown identifier '{node.name}'."
                )
                return UNKNOWN

            return self.variables[node.name]

        return ANY

    def _resolve_type(self, name: str) -> CardinalType:
        types = {
            "Int": INT,
            "Float": FLOAT,
            "Bool": BOOL,
            "String": STRING,
            "Any": ANY,
        }

        return types.get(name, CardinalType(
            kind=UNKNOWN.kind,
            name=name,
        ))

    def _compatible(
        self,
        expected: CardinalType,
        actual: CardinalType,
    ) -> bool:
        if expected == ANY or actual == UNKNOWN:
            return True

        return expected == actual

    def _error(self, message: str) -> None:
        self.errors.append(message)
