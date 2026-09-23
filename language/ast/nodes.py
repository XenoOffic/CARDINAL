from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ASTNode:
    """Base class for every CARDINAL AST node."""

    pass


@dataclass
class Program(ASTNode):
    declarations: list[ASTNode] = field(default_factory=list)


@dataclass
class Identifier(ASTNode):
    name: str
    type_name: str | None = None


@dataclass
class Literal(ASTNode):
    value: Any


@dataclass
class VariableDeclaration(ASTNode):
    name: str
    type_name: str | None
    value: ASTNode | None
    constant: bool = False


@dataclass
class FunctionDeclaration(ASTNode):
    name: str
    parameters: list[Identifier]
    return_type: str | None
    body: list[ASTNode] = field(default_factory=list)


@dataclass
class AgentDeclaration(ASTNode):
    """
    Declares an autonomous CARDINAL agent.

    An agent owns:
    - persistent state variables
    - behaviors
    - functions
    """

    name: str
    parent: str | None
    members: list[ASTNode] = field(default_factory=list)

    @property
    def variables(self) -> list[VariableDeclaration]:
        """Return all state variables declared by the agent."""

        return [
            member
            for member in self.members
            if isinstance(member, VariableDeclaration)
        ]

    @property
    def behaviors(self) -> list[BehaviorDeclaration]:
        """Return all behaviors declared by the agent."""

        return [
            member
            for member in self.members
            if isinstance(member, BehaviorDeclaration)
        ]

    @property
    def functions(self) -> list[FunctionDeclaration]:
        """Return all functions declared by the agent."""

        return [
            member
            for member in self.members
            if isinstance(member, FunctionDeclaration)
        ]


@dataclass
class BehaviorDeclaration(ASTNode):
    """
    Declares an executable behavior owned by an agent.
    """

    name: str
    body: list[ASTNode] = field(default_factory=list)


@dataclass
class ReturnStatement(ASTNode):
    value: ASTNode | None = None


@dataclass
class BinaryExpression(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode


@dataclass
class UnaryExpression(ASTNode):
    operator: str
    operand: ASTNode


@dataclass
class FunctionCall(ASTNode):
    name: str
    arguments: list[ASTNode] = field(default_factory=list)


@dataclass
class IfStatement(ASTNode):
    condition: ASTNode
    then_body: list[ASTNode] = field(default_factory=list)
    else_body: list[ASTNode] = field(default_factory=list)


@dataclass
class WhileStatement(ASTNode):
    condition: ASTNode
    body: list[ASTNode] = field(default_factory=list)


@dataclass
class AssignmentExpression(ASTNode):
    target: str
    operator: str
    value: ASTNode
