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
    name: str
    parent: str | None
    members: list[ASTNode] = field(default_factory=list)


@dataclass
class BehaviorDeclaration(ASTNode):
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
