from __future__ import annotations

from language.ast import (
    AgentDeclaration,
    AssignmentExpression,
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
            if isinstance(declaration, FunctionDeclaration):
                self._function(declaration)

            elif isinstance(declaration, AgentDeclaration):
                self._agent(declaration)

            else:
                self._declaration(declaration)

        main.emit(Instruction(OpCode.HALT))
        self.module.add_function(main)

        return self.module

    def _function(self, node: FunctionDeclaration) -> None:
        function = IRFunction(
            name=node.name,
            parameters=[
                parameter.name
                for parameter in node.parameters
            ],
        )

        previous_function = self.current_function
        self.current_function = function

        for statement in node.body:
            self._declaration(statement)

        if not function.instructions or (
            function.instructions[-1].opcode
            != OpCode.RETURN
        ):
            function.emit(Instruction(OpCode.RETURN))

        self.module.add_function(function)

        self.current_function = previous_function

    def _agent(self, node: AgentDeclaration) -> None:
        for member in node.members:
            if isinstance(member, FunctionDeclaration):
                self._function(member)

            elif isinstance(member, VariableDeclaration):
                self._declaration(member)

    def _declaration(self, node) -> None:
        if isinstance(node, VariableDeclaration):
            self._variable(node)

        elif isinstance(node, AssignmentExpression):
            self._expression(node)

        elif isinstance(node, IfStatement):
            self._if_statement(node)

        elif isinstance(node, WhileStatement):
            self._while_statement(node)

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

        self._emit(
            Instruction(OpCode.RETURN)
        )

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

        if isinstance(node, AssignmentExpression):
            self._assignment(node)
            return

        if isinstance(node, UnaryExpression):
            self._unary(node)
            return

        if isinstance(node, BinaryExpression):
            self._binary(node)
            return

        if isinstance(node, FunctionCall):
            for argument in node.arguments:
                self._expression(argument)

            self._emit(
                Instruction(
                    OpCode.CALL,
                    node.name,
                )
            )
            return

        raise TypeError(
            f"Unsupported AST node: {type(node).__name__}"
        )

    def _unary(self, node: UnaryExpression) -> None:
        self._expression(node.operand)

        opcode_map = {
            "-": OpCode.NEGATE,
            "!": OpCode.NOT,
        }

        opcode = opcode_map.get(node.operator)

        if opcode is None:
            raise ValueError(
                f"Unsupported unary operator: {node.operator}"
            )

        self._emit(
            Instruction(opcode)
        )

    def _binary(self, node: BinaryExpression) -> None:
        self._expression(node.left)
        self._expression(node.right)

        self._emit(
            Instruction(
                self._binary_opcode(node.operator)
            )
        )

    def _if_statement(self, node: IfStatement) -> None:
        self._expression(node.condition)

        jump_if_false = len(
            self.current_function.instructions
        )

        self._emit(
            Instruction(
                OpCode.JUMP_IF_FALSE,
                None,
            )
        )

        for statement in node.then_body:
            self._declaration(statement)

        if node.else_body:
            jump_end = len(
                self.current_function.instructions
            )

            self._emit(
                Instruction(
                    OpCode.JUMP,
                    None,
                )
            )

            else_start = len(
                self.current_function.instructions
            )

            self.current_function.instructions[
                jump_if_false
            ] = Instruction(
                OpCode.JUMP_IF_FALSE,
                else_start,
            )

            for statement in node.else_body:
                self._declaration(statement)

            end = len(
                self.current_function.instructions
            )

            self.current_function.instructions[
                jump_end
            ] = Instruction(
                OpCode.JUMP,
                end,
            )

        else:
            end = len(
                self.current_function.instructions
            )

            self.current_function.instructions[
                jump_if_false
            ] = Instruction(
                OpCode.JUMP_IF_FALSE,
                end,
            )

    def _while_statement(self, node: WhileStatement) -> None:
        loop_start = len(
            self.current_function.instructions
        )

        self._expression(node.condition)

        jump_exit = len(
            self.current_function.instructions
        )

        self._emit(
            Instruction(
                OpCode.JUMP_IF_FALSE,
                None,
            )
        )

        for statement in node.body:
            self._declaration(statement)

        self._emit(
            Instruction(
                OpCode.JUMP,
                loop_start,
            )
        )

        loop_end = len(
            self.current_function.instructions
        )

        self.current_function.instructions[
            jump_exit
        ] = Instruction(
            OpCode.JUMP_IF_FALSE,
            loop_end,
        )

    def _assignment(
        self,
        expression: AssignmentExpression,
    ) -> None:
        if expression.operator == "=":
            self._expression(expression.value)

            self._emit(
                Instruction(
                    OpCode.ASSIGN,
                    expression.target,
                )
            )
            return

        self._emit(
            Instruction(
                OpCode.LOAD,
                expression.target,
            )
        )

        self._expression(expression.value)

        operator_map = {
            "+=": OpCode.ADD,
            "-=": OpCode.SUB,
            "*=": OpCode.MUL,
            "/=": OpCode.DIV,
        }

        opcode = operator_map.get(
            expression.operator
        )

        if opcode is None:
            raise ValueError(
                "Unsupported assignment operator: "
                f"{expression.operator}"
            )

        self._emit(
            Instruction(opcode)
        )

        self._emit(
            Instruction(
                OpCode.ASSIGN,
                expression.target,
            )
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

            "&&": OpCode.AND,
            "||": OpCode.OR,
        }

        if operator not in operators:
            raise ValueError(
                f"Unsupported binary operator: {operator}"
            )

        return operators[operator]

    def _emit(self, instruction: Instruction) -> None:
        if self.current_function is None:
            raise RuntimeError(
                "IR generator has no active function."
            )

        self.current_function.emit(instruction)
