from cardinal import CardinalPipeline
from compiler.ir import IRAgent, IRBehavior


def test_agent_is_compiled_into_ir():
    source = """
    agent Counter {
        let value: Int = 0;

        behavior increment {
            value += 1;
        }
    }
    """

    module = CardinalPipeline().compile(source)

    agent = module.get_agent("Counter")

    assert isinstance(agent, IRAgent)
    assert agent.name == "Counter"
    assert agent.parent is None
    assert agent.state == ["value"]


def test_agent_behavior_is_compiled_into_ir():
    source = """
    agent Counter {
        let value: Int = 0;

        behavior increment {
            value += 1;
        }
    }
    """

    module = CardinalPipeline().compile(source)

    agent = module.get_agent("Counter")

    assert agent is not None

    behavior = agent.get_behavior("increment")

    assert isinstance(
        behavior,
        IRBehavior,
    )

    assert behavior.name == "increment"
    assert len(behavior.instructions) > 0


def test_agent_parent_is_preserved():
    source = """
    agent AdvancedCounter: Counter {
        let value: Int = 0;
    }
    """

    module = CardinalPipeline().compile(source)

    agent = module.get_agent(
        "AdvancedCounter"
    )

    assert agent is not None
    assert agent.parent == "Counter"


def test_agent_function_is_compiled():
    source = """
    agent Counter {
        let value: Int = 0;

        fn getValue() -> Int {
            return value;
        }
    }
    """

    module = CardinalPipeline().compile(source)

    agent = module.get_agent("Counter")

    assert agent is not None

    function = agent.get_function(
        "getValue"
    )

    assert function is not None
    assert function.name == "getValue"
