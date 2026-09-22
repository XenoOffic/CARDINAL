from compiler.ir import (
    IRFunction,
    IRModule,
    Instruction,
    OpCode,
)
from runtime.vm import VM


def test_function_call_with_parameters():
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

    main = IRFunction(
        name="main",
        instructions=[
            Instruction(OpCode.CONSTANT, 10),
            Instruction(OpCode.CONSTANT, 32),
            Instruction(OpCode.CALL, "add"),
            Instruction(OpCode.RETURN),
        ],
    )

    module = IRModule(
        name="test",
        functions=[add, main],
    )

    result = VM().execute(main, module)

    assert result == 42
