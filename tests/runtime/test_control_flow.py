from compiler.ir import (
    IRFunction,
    Instruction,
    OpCode,
)
from runtime.vm import VM


def test_jump_if_false():
    function = IRFunction(
        name="main",
        instructions=[
            Instruction(OpCode.CONSTANT, False),
            Instruction(OpCode.JUMP_IF_FALSE, 4),
            Instruction(OpCode.CONSTANT, "wrong"),
            Instruction(OpCode.RETURN),
            Instruction(OpCode.CONSTANT, "correct"),
            Instruction(OpCode.RETURN),
        ],
    )

    result = VM().execute(function)

    assert result == "correct"


def test_jump():
    function = IRFunction(
        name="main",
        instructions=[
            Instruction(OpCode.JUMP, 3),
            Instruction(OpCode.CONSTANT, "wrong"),
            Instruction(OpCode.RETURN),
            Instruction(OpCode.CONSTANT, "correct"),
            Instruction(OpCode.RETURN),
        ],
    )

    result = VM().execute(function)

    assert result == "correct"
