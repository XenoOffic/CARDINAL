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
    CardinalType,
)


class SemanticError(Exception):
    """Raised when CARDINAL code is semantically invalid."""


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.variables: dict[str, CardinalType] = {}
        self.functions: dict[str, FunctionDeclaration] = {}
        self.agents: set[str] = set()
        self.errors: list[str] = []

        self.current_function: FunctionDeclaration | None = None
        self.current_return_type: CardinalType = ANY
        self.current_function_has_return = False

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
        self.variables = {}

        for member in node.members:
            if isinstance(member, BehaviorDeclaration):
                for statement in member.body:
                    self._statement(statement)

            elif isinstance(member, VariableDeclaration):
                self._variable(member)

            elif isinstance(member, FunctionDeclaration):
                self._function(member)

        self.variables = previous_variables

    def _function(self, node: FunctionDeclaration) -> None:
        previous_variables = self.variables
        previous_function = self.current_function
        previous_return_type = self.current_return_type
        previous_has_return = self.current_function_has_return

        self.variables = {}
        self.current_function = node
        self.current_function_has_return = False

        if node.return_type is None:
            self.current_return_type = ANY
        else:
            self.current_return_type = self._resolve_type(
                node.return_type
            )

        for parameter in node.parameters:
            if parameter.name in self.variables:
                self._error(
                    f"Parameter '{parameter.name}' is already declared "
                    f"in function '{node.name}'."
                )
                continue

            if parameter.type_name is None:
                parameter_type = ANY
            else:
                parameter_type = self._resolve_type(
                    parameter.type_name
                )

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
            self._expression_type(node.condition)

            for statement in node.then_body:
                self._statement(statement)

            for statement in node.else_body:
                self._statement(statement)

        elif isinstance(node, WhileStatement):
            self._expression_type(node.condition)

            for statement in node.body:
                self._statement(statement)

        elif isinstance(node, AssignmentExpression):
            self._assignment(node)

        else:
            self._expression_type(node)

    def _return(self, node: ReturnStatement) -> None:
        self.current_function_has_return = True

        if self.current_function is None:
            self._error(
                "Return statement is only valid inside a function."
            )
            return

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

        value_type = self._expression_type(node.value)

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

        value_type = self._expression_type(node.value)
        variable_type = self.variables[node.target]

        if not self._compatible(
            variable_type,
            value_type,
        ):
            self._error(
                f"Cannot assign {value_type} to "
                f"variable '{node.target}' "
                f"of type {variable_type}."
            )

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

        if isinstance(node, FunctionCall):
            return self._function_call_type(node)

        if isinstance(node, BinaryExpression):
            left_type = self._expression_type(node.left)
            right_type = self._expression_type(node.right)

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

        if isinstance(node, AssignmentExpression):
            self._assignment(node)

            if node.target not in self.variables:
                return UNKNOWN

            return self.variables[node.target]

        return ANY

    def _function_call_type(
        self,
        node: FunctionCall,
    ) -> CardinalType:
        if node.name not in self.functions:
            self._error(
                f"Unknown function '{node.name}'."
            )

            for argument in node.arguments:
                self._expression_type(argument)

            return UNKNOWN

        function = self.functions[node.name]

        expected_count = len(function.parameters)
        actual_count = len(node.arguments)

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

            parameter = function.parameters[index]

            if parameter.type_name is None:
                continue

            parameter_type = self._resolve_type(
                parameter.type_name
            )

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

        if function.return_type is None:
            return ANY

        return self._resolve_type(
            function.return_type
        )

    def _resolve_type(self, name: str) -> CardinalType:
        types = {
            "Int": INT,
            "Float": FLOAT,
            "Bool": BOOL,
            "String": STRING,
            "Any": ANY,
        }

        return types.get(
            name,
            CardinalType(
                kind=UNKNOWN.kind,
                name=name,
            ),
        )

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
