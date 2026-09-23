from cardinal import CardinalPipeline
from runtime.vm import VM


def execute_function(
    source: str,
    function_name: str,
):
    pipeline = CardinalPipeline()
    module = pipeline.compile(source)

    function = next(
        function
        for function in module.functions
        if function.name == function_name
    )

    return VM().execute(
        function,
        module,
    )


def test_unary_negation():
    source = """
    fn calculate() -> Int {
        return -42;
    }
    """

    assert execute_function(
        source,
        "calculate",
    ) == -42


def test_unary_not():
    source = """
    fn calculate() -> Bool {
        return !true;
    }
    """

    assert execute_function(
        source,
        "calculate",
    ) is False


def test_logical_and():
    source = """
    fn calculate() -> Bool {
        return true && false;
    }
    """

    assert execute_function(
        source,
        "calculate",
    ) is False


def test_logical_or():
    source = """
    fn calculate() -> Bool {
        return true || false;
    }
    """

    assert execute_function(
        source,
        "calculate",
    ) is True


def test_combined_logical_expression():
    source = """
    fn calculate() -> Bool {
        return !(true && false) || false;
    }
    """

    assert execute_function(
        source,
        "calculate",
    ) is True


def test_invalid_unary_not_type():
    source = """
    fn calculate() -> Bool {
        return !42;
    }
    """

    try:
        CardinalPipeline().compile(source)
    except Exception:
        return

    raise AssertionError(
        "Expected semantic analysis to reject !42"
    )


def test_invalid_logical_operand_type():
    source = """
    fn calculate() -> Bool {
        return true && 42;
    }
    """

    try:
        CardinalPipeline().compile(source)
    except Exception:
        return

    raise AssertionError(
        "Expected semantic analysis to reject true && 42"
)
