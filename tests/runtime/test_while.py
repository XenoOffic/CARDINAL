from cardinal import CardinalPipeline


def test_while_loop():
    source = """
    let x: Int = 0;

    while x < 10 {
        x += 1;
    }
    """

    pipeline = CardinalPipeline()
    module = pipeline.compile(source)

    main = next(
        function
        for function in module.functions
        if function.name == "main"
    )

    pipeline_result = pipeline.run(source)

    assert main is not None
    assert pipeline_result is None
