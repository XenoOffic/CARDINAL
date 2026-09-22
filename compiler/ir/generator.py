from __future__ import annotations

from language.ast import (
    BinaryExpression,
    Identifier,
    Literal,
    Program,
    ReturnStatement,
    VariableDeclaration,
)

from .instructions import Instruction, OpCode
from .module import IRFunction, IRModule


class IRGenerator:
    """Converts CARDINAL AST nodes into intermediate representation."""

    def __init__(self) -> None:
        self.module = IRModule()
        self.current_function: IRFunction | None = None

    def generate(self, program: Program) -> IRModule:
        self.module = IRModule()

        main = IRFunction(name="main")
        self.current_function = main

        for declaration in program.declarations:
            self._declaration(declaration)

        main.emit(Instruction(OpCode.HALT))
        self.module.add_function(main)

        return self.module

    def _declaration(self, node) -> None:
        if isinstance(node, VariableDeclaration):
            self._variable(node)

        elif isinstance(node, ReturnStatement):
            self._return(node)

    def _variable(self, node: VariableDeclaration) -> None:
        if node.value is not None:
            self._expression(node.value)

        self._emit(
            Instruction(
                OpCode.STORE,
                node.name,
            )
        )

    def _return(self, node: ReturnStatement) -> None:
        if node.value is not None:
            self._expression(node.value)

        self._emit(Instruction(OpCode.RETURN))

    def _expression(self, node) -> None:
        if isinstance(node, Literal):
            self._emit(
                Instruction(
                    OpCode.CONSTANT,
                    node.value,
                )
            )
            return

        if isinstance(node, Identifier):
            self._emit(
                Instruction(
                    OpCode.LOAD,
                    node.name,
                )
            )
            return

        if isinstance(node, BinaryExpression):
            self._expression(node.left)
            self._expression(node.right)

            opcode = self._binary_opcode(node.operator)

            self._emit(
                Instruction(opcode)
            )
            return

        raise TypeError(
            f"Unsupported AST node: {type(node).__name__}"
        )

    def _binary_opcode(self, operator: str) -> OpCode:
        operators = {
            "+": OpCode.ADD,
            "-": OpCode.SUB,
            "*": OpCode.MUL,
            "/": OpCode.DIV,
            "%": OpCode.MOD,

            "==": OpCode.EQUAL,
            "!=": OpCode.NOT_EQUAL,
            "<": OpCode.LESS,
            "<=": OpCode.LESS_EQUAL,
            ">": OpCode.GREATER,
            ">=": OpCode.GREATER_EQUAL,
        }

        try:
            return operators[operator]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported binary operator: {operator}"
            ) from exc

    def _emit(self, instruction: Instruction) -> None:
        if self.current_function is None:
            raise RuntimeError(
                "IR generator has no active function."
            )

        self.current_function.emit(instruction)
