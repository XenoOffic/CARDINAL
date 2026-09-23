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

from .instructions import Instruction, OpCode
from .module import (
    IRAgent,
    IRBehavior,
    IRFunction,
    IRModule,
)


class IRGenerator:
    """Converts CARDINAL AST nodes into intermediate representation."""

    def __init__(self) -> None:
        self.module = IRModule()
        self.current_function: IRFunction | None = None
        self.current_behavior: IRBehavior | None = None
        self.current_agent: IRAgent | None = None

        self.agent_function_names: set[str] = set()

    def generate(self, program: Program) -> IRModule:
        self.module = IRModule()
        self.current_function = None
        self.current_behavior = None
        self.current_agent = None
        self.agent_function_names = set()

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

        self.current_function = None

        return self.module

    def _function(
        self,
        node: FunctionDeclaration,
        target_agent: IRAgent | None = None,
    ) -> IRFunction:
        function = IRFunction(
            name=node.name,
            parameters=[
                parameter.name
                for parameter in node.parameters
            ],
        )

        previous_function = self.current_function
        previous_behavior = self.current_behavior
        previous_agent = self.current_agent

        self.current_function = function
        self.current_behavior = None

        if target_agent is not None:
            self.current_agent = target_agent

        for statement in node.body:
            self._declaration(statement)

        if (
            not function.instructions
            or function.instructions[-1].opcode
            != OpCode.RETURN
        ):
            function.emit(
                Instruction(OpCode.RETURN)
            )

        if target_agent is not None:
            target_agent.add_function(function)

        self.module.add_function(function)

        self.current_function = previous_function
        self.current_behavior = previous_behavior
        self.current_agent = previous_agent

        return function

    def _agent(
        self,
        node: AgentDeclaration,
    ) -> None:
        agent = IRAgent(
            name=node.name,
            parent=node.parent,
        )

        previous_agent = self.current_agent
        previous_function = self.current_function
        previous_behavior = self.current_behavior

        self.current_agent = agent
        self.current_behavior = None

        self.agent_function_names = {
            member.name
            for member in node.members
            if isinstance(
                member,
                FunctionDeclaration,
            )
        }

        for member in node.members:
            if isinstance(
                member,
                VariableDeclaration,
            ):
                initial_value = None

                if isinstance(
                    member.value,
                    Literal,
                ):
                    initial_value = member.value.value

                agent.add_state(
                    member.name,
                    initial_value,
                )

            elif isinstance(
                member,
                BehaviorDeclaration,
            ):
                self._behavior(
                    member,
                    agent,
                )

            elif isinstance(
                member,
                FunctionDeclaration,
            ):
                self._function(
                    member,
                    target_agent=agent,
                )

        self.module.add_agent(agent)

        self.current_agent = previous_agent
        self.current_function = previous_function
        self.current_behavior = previous_behavior
        self.agent_function_names = set()

    def _behavior(
        self,
        node: BehaviorDeclaration,
        agent: IRAgent,
    ) -> IRBehavior:
        behavior = IRBehavior(
            name=node.name,
        )

        previous_behavior = self.current_behavior
        previous_function = self.current_function
        previous_agent = self.current_agent

        self.current_behavior = behavior
        self.current_function = None
        self.current_agent = agent

        for statement in node.body:
            self._declaration(statement)

        if (
            not behavior.instructions
            or behavior.instructions[-1].opcode
            != OpCode.RETURN
        ):
            behavior.emit(
                Instruction(OpCode.RETURN)
            )

        agent.add_behavior(behavior)

        self.current_behavior = previous_behavior
        self.current_function = previous_function
        self.current_agent = previous_agent

        return behavior

    def _declaration(self, node) -> None:
        if isinstance(node, VariableDeclaration):
            self._variable(node)

        elif isinstance(node, AssignmentExpression):
            self._expression(node)

        elif isinstance(node, FunctionCall):
            self._expression(node)

        elif isinstance(node, IfStatement):
            self._if_statement(node)

        elif isinstance(node, WhileStatement):
            self._while_statement(node)

        elif isinstance(node, ReturnStatement):
            self._return(node)

        elif isinstance(node, list):
            self._block(node)

    def _block(self, statements: list) -> None:
        self._emit(
            Instruction(OpCode.ENTER_SCOPE)
        )

        for statement in statements:
            self._declaration(statement)

        self._emit(
            Instruction(OpCode.EXIT_SCOPE)
        )

    def _variable(
        self,
        node: VariableDeclaration,
    ) -> None:
        if node.value is not None:
            self._expression(node.value)

        self._emit(
            Instruction(
                OpCode.STORE,
                node.name,
            )
        )

    def _return(
        self,
        node: ReturnStatement,
    ) -> None:
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

            if (
                self.current_agent is not None
                and node.name
                in self.agent_function_names
            ):
                self._emit(
                    Instruction(
                        OpCode.CALL_AGENT,
                        node.name,
                    )
                )
            else:
                self._emit(
                    Instruction(
                        OpCode.CALL,
                        node.name,
                    )
                )

            return

        raise TypeError(
            f"Unsupported AST node: "
            f"{type(node).__name__}"
        )

    def _unary(
        self,
        node: UnaryExpression,
    ) -> None:
        self._expression(node.operand)

        opcode_map = {
            "-": OpCode.NEGATE,
            "!": OpCode.NOT,
        }

        opcode = opcode_map.get(
            node.operator
        )

        if opcode is None:
            raise ValueError(
                "Unsupported unary operator: "
                f"{node.operator}"
            )

        self._emit(
            Instruction(opcode)
        )

    def _binary(
        self,
        node: BinaryExpression,
    ) -> None:
        self._expression(node.left)
        self._expression(node.right)

        self._emit(
            Instruction(
                self._binary_opcode(
                    node.operator
                )
            )
        )

    def _if_statement(
        self,
        node: IfStatement,
    ) -> None:
        self._expression(node.condition)

        jump_if_false = len(
            self._instructions()
        )

        self._emit(
            Instruction(
                OpCode.JUMP_IF_FALSE,
                None,
            )
        )

        self._block(node.then_body)

        if node.else_body:
            jump_end = len(
                self._instructions()
            )

            self._emit(
                Instruction(
                    OpCode.JUMP,
                    None,
                )
            )

            else_start = len(
                self._instructions()
            )

            self._replace_instruction(
                jump_if_false,
                Instruction(
                    OpCode.JUMP_IF_FALSE,
                    else_start,
                ),
            )

            self._block(node.else_body)

            end = len(
                self._instructions()
            )

            self._replace_instruction(
                jump_end,
                Instruction(
                    OpCode.JUMP,
                    end,
                ),
            )

        else:
            end = len(
                self._instructions()
            )

            self._replace_instruction(
                jump_if_false,
                Instruction(
                    OpCode.JUMP_IF_FALSE,
                    end,
                ),
            )

    def _while_statement(
        self,
        node: WhileStatement,
    ) -> None:
        loop_start = len(
            self._instructions()
        )

        self._expression(node.condition)

        jump_exit = len(
            self._instructions()
        )

        self._emit(
            Instruction(
                OpCode.JUMP_IF_FALSE,
                None,
            )
        )

        self._block(node.body)

        self._emit(
            Instruction(
                OpCode.JUMP,
                loop_start,
            )
        )

        loop_end = len(
            self._instructions()
        )

        self._replace_instruction(
            jump_exit,
            Instruction(
                OpCode.JUMP_IF_FALSE,
                loop_end,
            ),
        )

    def _assignment(
        self,
        expression: AssignmentExpression,
    ) -> None:
        if expression.operator == "=":
            self._expression(
                expression.value
            )

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

        self._expression(
            expression.value
        )

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

    def _binary_opcode(
        self,
        operator: str,
    ) -> OpCode:
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
                f"Unsupported binary operator: "
                f"{operator}"
            )

        return operators[operator]

    def _instructions(self) -> list[Instruction]:
        if self.current_behavior is not None:
            return self.current_behavior.instructions

        if self.current_function is not None:
            return self.current_function.instructions

        raise RuntimeError(
            "IR generator has no active instruction stream."
        )

    def _emit(
        self,
        instruction: Instruction,
    ) -> None:
        self._instructions().append(
            instruction
        )

    def _replace_instruction(
        self,
        index: int,
        instruction: Instruction,
    ) -> None:
        self._instructions()[index] = instruction
