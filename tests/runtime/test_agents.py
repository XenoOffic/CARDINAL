from cardinal import CardinalPipeline
from runtime.vm import AgentInstance, VM


def test_agent_can_be_spawned():
    source = """
    agent Counter {
        let value: Int = 0;

        behavior increment {
            value += 1;
        }
    }
    """

    module = CardinalPipeline().compile(source)

    vm = VM()

    agent = module.get_agent("Counter")

    assert agent is not None

    instance = vm.spawn_agent(agent)

    assert isinstance(
        instance,
        AgentInstance,
    )

    assert instance.name == "Counter"
    assert instance.state["value"] == 0


def test_agent_behavior_changes_persistent_state():
    source = """
    agent Counter {
        let value: Int = 0;

        behavior increment {
            value += 1;
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
        "increment",
        module,
    )

    assert instance.state["value"] == 1

    vm.execute_behavior(
        instance,
        "increment",
        module,
    )

    assert instance.state["value"] == 2


def test_multiple_agent_instances_have_independent_state():
    source = """
    agent Counter {
        let value: Int = 0;

        behavior increment {
            value += 1;
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
        "increment",
        module,
    )

    assert first.state["value"] == 1
    assert second.state["value"] == 0


def test_unknown_behavior_raises_vm_error():
    source = """
    agent Counter {
        let value: Int = 0;
    }
    """

    module = CardinalPipeline().compile(source)

    vm = VM()

    instance = vm.spawn_agent_by_name(
        module,
        "Counter",
    )

    try:
        vm.execute_behavior(
            instance,
            "missing",
            module,
        )
    except Exception:
        return

    raise AssertionError(
        "Expected unknown behavior to fail."
    )
