from compiler.ir import (
    IRFunction,
    IRModule,
    Instruction,
    OpCode,
)
from runtime.vm import VM


def test_nested_function_calls():
    add = IRFunction(
        name="add",
        parameters=["a", "b"],
        instructions=[
            Instruction(OpCode.LOAD, "a"),
            Instruction(OpCode.LOAD, "b"),
            Instruction(OpCode.ADD),
            Instruction(OpCode.RETURN),
        ],
    )

    multiply = IRFunction(
        name="multiply",
        parameters=["a", "b"],
        instructions=[
            Instruction(OpCode.LOAD, "a"),
            Instruction(OpCode.LOAD, "b"),
            Instruction(OpCode.MUL),

            Instruction(OpCode.CONSTANT, 2),
            Instruction(OpCode.CALL, "add"),

            Instruction(OpCode.RETURN),
        ],
    )

    main = IRFunction(
        name="main",
        instructions=[
            Instruction(OpCode.CONSTANT, 6),
            Instruction(OpCode.CONSTANT, 7),
            Instruction(OpCode.CALL, "multiply"),
            Instruction(OpCode.RETURN),
        ],
    )

    module = IRModule()
    module.add_function(add)
    module.add_function(multiply)
    module.add_function(main)

    result = VM().execute(main, module)

    assert result == 44
