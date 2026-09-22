from cardinal import CardinalPipeline


def test_pipeline_executes_expression():
    source = """
    let answer: Int = 10 + 32;
    """

    pipeline = CardinalPipeline()
    module = pipeline.compile(source)

    assert len(module.functions) == 1
    assert module.functions[0].name == "main"


def test_pipeline_executes_return():
    source = """
    fn main_value() -> Int {
        return 42;
    }
    """

    pipeline = CardinalPipeline()

    module = pipeline.compile(source)

    assert module.functions
