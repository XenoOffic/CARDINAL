from cardinal import CardinalPipeline
from runtime.vm import VM


def test_agent_function_can_be_called_by_behavior():
    source = """
    agent Counter {
        let value: Int = 0;

        fn increment() -> Unit {
            value += 1;
            return;
        }

        behavior tick {
            increment();
        }
    }
    """

    module = CardinalPipeline().compile(source)

    vm = VM()

    instance = vm.spawn_agent_by_name(
        module,
        "Counter",
    )

    vm.execute_behavior(
        instance,
        "tick",
        module,
    )

    assert instance.state["value"] == 1


def test_agent_function_can_be_called_multiple_times():
    source = """
    agent Counter {
        let value: Int = 0;

        fn increment() -> Unit {
            value += 1;
            return;
        }

        behavior tick {
            increment();
            increment();
        }
    }
    """

    module = CardinalPipeline().compile(source)

    vm = VM()

    instance = vm.spawn_agent_by_name(
        module,
        "Counter",
    )

    vm.execute_behavior(
        instance,
        "tick",
        module,
    )

    assert instance.state["value"] == 2


def test_agent_instances_keep_function_state_independent():
    source = """
    agent Counter {
        let value: Int = 0;

        fn increment() -> Unit {
            value += 1;
            return;
        }

        behavior tick {
            increment();
        }
    }
    """

    module = CardinalPipeline().compile(source)

    vm = VM()

    first = vm.spawn_agent_by_name(
        module,
        "Counter",
    )

    second = vm.spawn_agent_by_name(
        module,
        "Counter",
    )

    vm.execute_behavior(
        first,
        "tick",
        module,
    )

    assert first.state["value"] == 1
    assert second.state["value"] == 0


def test_agent_function_can_return_value():
    source = """
    agent Counter {
        let value: Int = 10;

        fn getValue() -> Int {
            return value;
        }

        behavior read {
            return getValue();
        }
    }
    """

    module = CardinalPipeline().compile(source)

    vm = VM()

    instance = vm.spawn_agent_by_name(
        module,
        "Counter",
    )

    result = vm.execute_behavior(
        instance,
        "read",
        module,
    )

    assert result == 10
