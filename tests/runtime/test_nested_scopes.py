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


def test_nested_scope_shadowing():
    source = """
    fn calculate() -> Int {
        let x: Int = 10;

        {
            let x: Int = 20;
        }

        return x;
    }
    """

    assert execute_function(
        source,
        "calculate",
    ) == 10


def test_nested_scope_can_read_outer_variable():
    source = """
    fn calculate() -> Int {
        let x: Int = 10;

        {
            let y: Int = x + 5;
            return y;
        }
    }
    """

    assert execute_function(
        source,
        "calculate",
    ) == 15


def test_nested_scope_assignment_updates_outer_variable():
    source = """
    fn calculate() -> Int {
        let x: Int = 10;

        {
            x = 25;
        }

        return x;
    }
    """

    assert execute_function(
        source,
        "calculate",
    ) == 25


def test_if_scope_isolated():
    source = """
    fn calculate() -> Int {
        let x: Int = 10;

        if true {
            let x: Int = 99;
        }

        return x;
    }
    """

    assert execute_function(
        source,
        "calculate",
    ) == 10


def test_while_scope_isolated():
    source = """
    fn calculate() -> Int {
        let x: Int = 10;
        let counter: Int = 0;

        while counter < 1 {
            let x: Int = 99;
            counter += 1;
        }

        return x;
    }
    """

    assert execute_function(
        source,
        "calculate",
    ) == 10


def test_nested_scope_does_not_leak_variable():
    source = """
    fn calculate() -> Int {
        {
            let hidden: Int = 42;
        }

        return hidden;
    }
    """

    try:
        CardinalPipeline().compile(source)
    except Exception:
        return

    raise AssertionError(
        "Expected hidden variable to remain outside its scope."
  )
