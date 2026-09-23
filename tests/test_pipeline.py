from cardinal import CardinalPipeline
from runtime.vm import VM


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


def test_pipeline_executes_function_call():
    source = """
    fn add(a: Int, b: Int) -> Int {
        return a + b;
    }

    fn calculate() -> Int {
        return add(10, 32);
    }
    """

    pipeline = CardinalPipeline()
    module = pipeline.compile(source)

    calculate = next(
        function
        for function in module.functions
        if function.name == "calculate"
    )

    result = VM().execute(
        calculate,
        module,
    )

    assert result == 42


def test_pipeline_executes_nested_function_calls():
    source = """
    fn add(a: Int, b: Int) -> Int {
        return a + b;
    }

    fn double(value: Int) -> Int {
        return add(value, value);
    }

    fn calculate() -> Int {
        return double(21);
    }
    """

    pipeline = CardinalPipeline()
    module = pipeline.compile(source)

    calculate = next(
        function
        for function in module.functions
        if function.name == "calculate"
    )

    result = VM().execute(
        calculate,
        module,
    )

    assert result == 42
