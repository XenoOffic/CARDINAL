from compiler.ir import IRFunction, Instruction, OpCode
from runtime.vm import VM


def test_vm_addition():
    function = IRFunction(
        name="main",
        instructions=[
            Instruction(OpCode.CONSTANT, 10),
            Instruction(OpCode.CONSTANT, 32),
            Instruction(OpCode.ADD),
            Instruction(OpCode.RETURN),
        ],
    )

    result = VM().execute(function)

    assert result == 42


def test_vm_variables():
    function = IRFunction(
        name="main",
        instructions=[
            Instruction(OpCode.CONSTANT, 123),
            Instruction(OpCode.STORE, "answer"),
            Instruction(OpCode.LOAD, "answer"),
            Instruction(OpCode.RETURN),
        ],
    )

    result = VM().execute(function)

    assert result == 123
