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

from language.types import (
    ANY,
    BOOL,
    FLOAT,
    INT,
    STRING,
    UNKNOWN,
    UNIT,
    CardinalType,
    TypeKind,
    function_type,
)


class SemanticError(Exception):
    """Raised when CARDINAL code is semantically invalid."""


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.variables: dict[str, CardinalType] = {}
        self.functions: dict[str, FunctionDeclaration] = {}
        self.function_types: dict[str, CardinalType] = {}
        self.agents: set[str] = set()
        self.errors: list[str] = []

        self.current_function: FunctionDeclaration | None = None
        self.current_return_type: CardinalType = ANY
        self.current_function_has_return = False
        self.inside_behavior = False

    def analyze(self, program: Program) -> None:
        self._collect_functions(program)

        for declaration in program.declarations:
            self._declaration(declaration)

        if self.errors:
            raise SemanticError("\n".join(self.errors))

    def _collect_functions(self, program: Program) -> None:
        for declaration in program.declarations:
            if isinstance(declaration, FunctionDeclaration):
                self._register_function(declaration)

            elif isinstance(declaration, AgentDeclaration):
                for member in declaration.members:
                    if isinstance(member, FunctionDeclaration):
                        self._register_function(member)

    def _register_function(
        self,
        node: FunctionDeclaration,
    ) -> None:
        if node.name in self.functions:
            self._error(
                f"Function '{node.name}' is already declared."
            )
            return

        self.functions[node.name] = node

        parameter_types: list[CardinalType] = []

        for parameter in node.parameters:
            if parameter.type_name is None:
                parameter_types.append(ANY)
            else:
                parameter_types.append(
                    self._resolve_type(
                        parameter.type_name
                    )
                )

        if node.return_type is None:
            return_type = ANY
        else:
            return_type = self._resolve_type(
                node.return_type
            )

        self.function_types[node.name] = function_type(
            parameter_types,
            return_type,
        )

    def _declaration(self, node) -> None:
        if isinstance(node, AgentDeclaration):
            self._agent(node)

        elif isinstance(node, FunctionDeclaration):
            self._function(node)

        elif isinstance(node, VariableDeclaration):
            self._variable(node)

        elif isinstance(node, WhileStatement):
            self._statement(node)

        elif isinstance(node, IfStatement):
            self._statement(node)

        elif isinstance(node, AssignmentExpression):
            self._statement(node)

    def _agent(self, node: AgentDeclaration) -> None:
        if node.name in self.agents:
            self._error(
                f"Agent '{node.name}' is already declared."
            )
            return

        self.agents.add(node.name)

        previous_variables = self.variables
        previous_behavior = self.inside_behavior

        self.variables = {}

        for member in node.members:
            if isinstance(member, BehaviorDeclaration):
                self._behavior(member)

            elif isinstance(member, VariableDeclaration):
                self._variable(member)

            elif isinstance(member, FunctionDeclaration):
                self._function(member)

        self.variables = previous_variables
        self.inside_behavior = previous_behavior

    def _behavior(self, node: BehaviorDeclaration) -> None:
        previous_behavior = self.inside_behavior

        self.inside_behavior = True

        for statement in node.body:
            self._statement(statement)

        self.inside_behavior = previous_behavior

    def _function(self, node: FunctionDeclaration) -> None:
        previous_variables = self.variables
        previous_function = self.current_function
        previous_return_type = self.current_return_type
        previous_has_return = self.current_function_has_return
        previous_behavior = self.inside_behavior

        self.variables = {}
        self.current_function = node
        self.inside_behavior = False
        self.current_function_has_return = False

        function_signature = self.function_types.get(
            node.name
        )

        if function_signature is None:
            self._register_function(node)
            function_signature = self.function_types[
                node.name
            ]

        self.current_return_type = (
            function_signature.return_type
            if function_signature.return_type is not None
            else ANY
        )

        for index, parameter in enumerate(
            node.parameters
        ):
            parameter_type = (
                function_signature.parameters[index]
            )

            if parameter.name in self.variables:
                self._error(
                    f"Parameter '{parameter.name}' is already "
                    f"declared in function '{node.name}'."
                )
                continue

            self.variables[parameter.name] = parameter_type

        for statement in node.body:
            self._statement(statement)

        if (
            node.return_type is not None
            and self.current_return_type != ANY
            and self.current_return_type != UNKNOWN
            and not self.current_function_has_return
        ):
            self._error(
                f"Function '{node.name}' must return "
                f"{self.current_return_type}."
            )

        self.variables = previous_variables
        self.current_function = previous_function
        self.current_return_type = previous_return_type
        self.current_function_has_return = previous_has_return
        self.inside_behavior = previous_behavior

    def _variable(self, node: VariableDeclaration) -> None:
        if node.name in self.variables:
            self._error(
                f"Variable '{node.name}' is already declared."
            )
            return

        value_type = UNKNOWN

        if node.value is not None:
            value_type = self._expression_type(
                node.value
            )

        if node.type_name is not None:
            declared_type = self._resolve_type(
                node.type_name
            )

            if not self._compatible(
                declared_type,
                value_type,
            ):
                self._error(
                    f"Cannot assign {value_type} to "
                    f"variable '{node.name}' of type "
                    f"{declared_type}."
                )

            value_type = declared_type

        self.variables[node.name] = value_type

    def _statement(self, node) -> None:
        if isinstance(node, VariableDeclaration):
            self._variable(node)

        elif isinstance(node, ReturnStatement):
            self._return(node)

        elif isinstance(node, IfStatement):
            condition_type = self._expression_type(
                node.condition
            )

            if (
                condition_type != BOOL
                and condition_type != ANY
                and condition_type != UNKNOWN
            ):
                self._error(
                    "If condition must be Bool."
                )

            for statement in node.then_body:
                self._statement(statement)

            for statement in node.else_body:
                self._statement(statement)

        elif isinstance(node, WhileStatement):
            condition_type = self._expression_type(
                node.condition
            )

            if (
                condition_type != BOOL
                and condition_type != ANY
                and condition_type != UNKNOWN
            ):
                self._error(
                    "While condition must be Bool."
                )

            for statement in node.body:
                self._statement(statement)

        elif isinstance(node, AssignmentExpression):
            self._assignment(node)

        else:
            self._expression_type(node)

    def _return(self, node: ReturnStatement) -> None:
        if self.current_function is None:
            if self.inside_behavior:
                return

            self._error(
                "Return statement is only valid inside "
                "a function or behavior."
            )
            return

        self.current_function_has_return = True

        if node.value is None:
            if (
                self.current_return_type != ANY
                and self.current_return_type != UNKNOWN
            ):
                self._error(
                    f"Function '{self.current_function.name}' "
                    f"must return {self.current_return_type}."
                )
            return

        value_type = self._expression_type(
            node.value
        )

        if not self._compatible(
            self.current_return_type,
            value_type,
        ):
            self._error(
                f"Function '{self.current_function.name}' "
                f"returns {self.current_return_type}, "
                f"but got {value_type}."
            )

    def _assignment(
        self,
        node: AssignmentExpression,
    ) -> None:
        if node.target not in self.variables:
            self._error(
                f"Unknown identifier '{node.target}'."
            )
            return

        value_type = self._expression_type(
            node.value
        )

        variable_type = self.variables[
            node.target
        ]

        if node.operator != "=":
            if node.operator in {
                "+=",
                "-=",
                "*=",
                "/=",
            }:
                if variable_type not in {
                    INT,
                    FLOAT,
                    ANY,
                    UNKNOWN,
                }:
                    self._error(
                        f"Compound assignment '{node.operator}' "
                        f"requires a numeric variable."
                    )

            else:
                self._error(
                    f"Unsupported assignment operator "
                    f"'{node.operator}'."
                )

        if not self._compatible(
            variable_type,
            value_type,
        ):
            self._error(
                f"Cannot assign {value_type} to "
                f"variable '{node.target}' "
                f"of type {variable_type}."
            )

    def _expression_type(
        self,
        node,
    ) -> CardinalType:
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

        if isinstance(node, FunctionCall):
            return self._function_call_type(node)

        if isinstance(node, UnaryExpression):
            return self._unary_type(node)

        if isinstance(node, BinaryExpression):
            return self._binary_type(node)

        if isinstance(node, AssignmentExpression):
            self._assignment(node)

            if node.target not in self.variables:
                return UNKNOWN

            return self.variables[node.target]

        return ANY

    def _unary_type(
        self,
        node: UnaryExpression,
    ) -> CardinalType:
        operand_type = self._expression_type(
            node.operand
        )

        if operand_type in {ANY, UNKNOWN}:
            return operand_type

        if node.operator == "-":
            if operand_type in {INT, FLOAT}:
                return operand_type

            self._error(
                f"Unary '-' requires a numeric operand, "
                f"got {operand_type}."
            )
            return UNKNOWN

        if node.operator == "!":
            if operand_type == BOOL:
                return BOOL

            self._error(
                f"Unary '!' requires a Bool operand, "
                f"got {operand_type}."
            )
            return UNKNOWN

        self._error(
            f"Unsupported unary operator "
            f"'{node.operator}'."
        )

        return UNKNOWN

    def _binary_type(
        self,
        node: BinaryExpression,
    ) -> CardinalType:
        left_type = self._expression_type(
            node.left
        )

        right_type = self._expression_type(
            node.right
        )

        if (
            left_type == UNKNOWN
            or right_type == UNKNOWN
        ):
            return UNKNOWN

        if node.operator in {
            "+",
            "-",
            "*",
            "/",
            "%",
        }:
            if (
                left_type == INT
                and right_type == INT
            ):
                return INT

            if (
                left_type in {INT, FLOAT}
                and right_type in {INT, FLOAT}
            ):
                return FLOAT

            if (
                node.operator == "+"
                and left_type == STRING
                and right_type == STRING
            ):
                return STRING

            self._error(
                f"Invalid operands for "
                f"'{node.operator}': "
                f"{left_type} and {right_type}."
            )

            return UNKNOWN

        if node.operator in {
            "==",
            "!=",
            "<",
            "<=",
            ">",
            ">=",
        }:
            return BOOL

        if node.operator in {
            "&&",
            "||",
        }:
            if (
                left_type != BOOL
                or right_type != BOOL
            ):
                self._error(
                    f"Logical operator '{node.operator}' "
                    f"requires Bool operands."
                )
                return UNKNOWN

            return BOOL

        self._error(
            f"Unsupported binary operator "
            f"'{node.operator}'."
        )

        return UNKNOWN

    def _function_call_type(
        self,
        node: FunctionCall,
    ) -> CardinalType:
        if node.name not in self.function_types:
            self._error(
                f"Unknown function '{node.name}'."
            )

            for argument in node.arguments:
                self._expression_type(argument)

            return UNKNOWN

        signature = self.function_types[
            node.name
        ]

        expected_count = len(
            signature.parameters
        )

        actual_count = len(
            node.arguments
        )

        if expected_count != actual_count:
            self._error(
                f"Function '{node.name}' expects "
                f"{expected_count} argument(s), "
                f"but got {actual_count}."
            )

        count = min(
            expected_count,
            actual_count,
        )

        for index in range(count):
            argument_type = self._expression_type(
                node.arguments[index]
            )

            parameter_type = signature.parameters[
                index
            ]

            if not self._compatible(
                parameter_type,
                argument_type,
            ):
                self._error(
                    f"Argument {index + 1} of function "
                    f"'{node.name}' expects "
                    f"{parameter_type}, "
                    f"but got {argument_type}."
                )

        for argument in node.arguments[count:]:
            self._expression_type(argument)

        return (
            signature.return_type
            if signature.return_type is not None
            else ANY
        )

    def _resolve_type(
        self,
        name: str,
    ) -> CardinalType:
        types = {
            "Int": INT,
            "Float": FLOAT,
            "Bool": BOOL,
            "String": STRING,
            "Unit": UNIT,
            "Any": ANY,
        }

        return types.get(
            name,
            CardinalType(
                kind=TypeKind.UNKNOWN,
                name=name,
            ),
        )

    def _compatible(
        self,
        expected: CardinalType,
        actual: CardinalType,
    ) -> bool:
        if expected == ANY:
            return True

        if actual == UNKNOWN:
            return True

        return expected == actual

    def _error(self, message: str) -> None:
        self.errors.append(message)
