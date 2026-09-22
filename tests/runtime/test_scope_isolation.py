from compiler.ir import (
    IRFunction,
    IRModule,
    Instruction,
    OpCode,
)
from runtime.vm import VM


def test_function_scope_is_isolated():
    set_value = IRFunction(
        name="set_value",
        parameters=[],
        instructions=[
            Instruction(OpCode.CONSTANT, 5),
            Instruction(OpCode.STORE, "x"),

            Instruction(OpCode.LOAD, "x"),
            Instruction(OpCode.RETURN),
        ],
    )

    main = IRFunction(
        name="main",
        instructions=[
            Instruction(OpCode.CONSTANT, 100),
            Instruction(OpCode.STORE, "x"),

            Instruction(OpCode.CALL, "set_value"),

            Instruction(OpCode.STORE, "result"),

            Instruction(OpCode.LOAD, "x"),
            Instruction(OpCode.RETURN),
        ],
    )

    module = IRModule()
    module.add_function(set_value)
    module.add_function(main)

    result = VM().execute(main, module)

    assert result == 100
