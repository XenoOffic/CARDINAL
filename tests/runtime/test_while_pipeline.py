from cardinal import CardinalPipeline


def test_while_pipeline():
    source = """
    let x: Int = 0;

    while x < 10 {
        x += 1;
    }
    """

    pipeline = CardinalPipeline()

    module = pipeline.compile(source)

    assert module is not None
    assert len(module.functions) > 0

    main = next(
        function
        for function in module.functions
        if function.name == "main"
    )

    assert main is not None

    opcodes = [
        instruction.opcode.name
        for instruction in main.instructions
    ]

    assert "STORE" in opcodes
    assert "LOAD" in opcodes
    assert "LESS" in opcodes
    assert "JUMP_IF_FALSE" in opcodes
    assert "JUMP" in opcodes
    assert "ASSIGN" in opcodes
