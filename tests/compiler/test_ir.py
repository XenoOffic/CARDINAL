from compiler.ir import IRGenerator, OpCode
from language.parser import Parser


def test_generate_string_variable():
    source = """
    let message: String = "Hello";
    """

    program = Parser.from_source(source).parse()
    module = IRGenerator().generate(program)

    instructions = module.functions[0].instructions

    assert instructions[0].opcode == OpCode.CONSTANT
    assert instructions[0].operand == "Hello"

    assert instructions[1].opcode == OpCode.STORE
    assert instructions[1].operand == "message"

    assert instructions[2].opcode == OpCode.HALT
