from compiler.ir import IRFunction, Instruction, OpCode
from runtime.vm import VM


def test_while_loop_vm():
    function = IRFunction(
        name="main",
        instructions=[
            # x = 0
            Instruction(OpCode.CONSTANT, 0),
            Instruction(OpCode.ASSIGN, "x"),

            # 2: LOAD x
            Instruction(OpCode.LOAD, "x"),

            # 3: CONSTANT 10
            Instruction(OpCode.CONSTANT, 10),

            # 4: x < 10
            Instruction(OpCode.LESS),

            # 5: exit if false
            Instruction(OpCode.JUMP_IF_FALSE, 12),

            # 6: LOAD x
            Instruction(OpCode.LOAD, "x"),

            # 7: CONSTANT 1
            Instruction(OpCode.CONSTANT, 1),

            # 8: x + 1
            Instruction(OpCode.ADD),

            # 9: x = x + 1
            Instruction(OpCode.ASSIGN, "x"),

            # 10: jump back to condition
            Instruction(OpCode.JUMP, 2),

            # 11: unused
            Instruction(OpCode.HALT),

            # 12: return x
            Instruction(OpCode.LOAD, "x"),
            Instruction(OpCode.RETURN),
        ],
    )

    result = VM().execute(function)

    assert result == 10
