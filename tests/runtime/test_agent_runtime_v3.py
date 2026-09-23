from __future__ import annotations

import pytest

from compiler.ir import (
    IRBehavior,
    IRAgent,
    IRModule,
    Instruction,
    OpCode,
)
from runtime.vm import VM
from runtime.vm.vm import (
    AgentEvent,
    AgentLifecycle,
    VMError,
)


def make_counter_agent() -> IRAgent:
    agent = IRAgent(
        name="Counter",
        state=["value"],
        initial_state={"value": 0},
    )

    behavior = IRBehavior(
        name="tick",
        instructions=[
            Instruction(
                OpCode.LOAD,
                "value",
            ),
            Instruction(
                OpCode.CONSTANT,
                1,
            ),
            Instruction(OpCode.ADD),
            Instruction(
                OpCode.ASSIGN,
                "value",
            ),
            Instruction(OpCode.RETURN),
        ],
    )

    agent.add_behavior(behavior)

    return agent


def test_agent_starts_created() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    assert agent.lifecycle == (
        AgentLifecycle.CREATED
    )


def test_agent_can_start() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    vm.start_agent(agent)

    assert agent.lifecycle == (
        AgentLifecycle.RUNNING
    )


def test_agent_can_stop() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    vm.start_agent(agent)
    vm.stop_agent(agent)

    assert agent.lifecycle == (
        AgentLifecycle.STOPPED
    )


def test_event_dispatch_selects_behavior() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    vm.bind_behavior(
        agent,
        "tick",
        "tick",
    )

    result = vm.dispatch_event(
        agent,
        AgentEvent("tick"),
    )

    assert result is None
    assert agent.state["value"] == 1


def test_event_type_can_select_behavior_directly() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    vm.dispatch_event(
        agent,
        AgentEvent("tick"),
    )

    assert agent.state["value"] == 1


def test_events_are_queued() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    agent.emit(
        AgentEvent("tick")
    )

    agent.emit(
        AgentEvent("tick")
    )

    assert len(agent.event_queue) == 2

    vm.run_until_idle(agent)

    assert len(agent.event_queue) == 0
    assert agent.state["value"] == 2


def test_vm_emit_event() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    vm.emit_event(
        agent,
        AgentEvent(
            type="tick",
            payload={"source": "test"},
        ),
    )

    assert len(agent.event_queue) == 1
    assert agent.event_queue[0].payload == {
        "source": "test"
    }


def test_event_counter_increments() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    vm.emit_event(
        agent,
        AgentEvent("tick"),
    )

    vm.emit_event(
        agent,
        AgentEvent("tick"),
    )

    vm.run_until_idle(agent)

    assert agent.context.events_processed == 2


def test_capabilities() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    assert not agent.context.has_capability(
        "network"
    )

    vm.grant_capability(
        agent,
        "network",
    )

    assert agent.context.has_capability(
        "network"
    )

    vm.require_capability(
        agent,
        "network",
    )

    vm.revoke_capability(
        agent,
        "network",
    )

    assert not agent.context.has_capability(
        "network"
    )


def test_missing_capability_raises() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    with pytest.raises(VMError):
        vm.require_capability(
            agent,
            "filesystem",
        )


def test_stopped_agent_cannot_receive_event() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    vm.stop_agent(agent)

    with pytest.raises(VMError):
        vm.emit_event(
            agent,
            AgentEvent("tick"),
        )


def test_stopped_agent_cannot_execute_behavior() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    vm.stop_agent(agent)

    with pytest.raises(VMError):
        vm.execute_behavior(
            agent,
            "tick",
        )


def test_instruction_budget_limits_execution() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    agent.context.max_instructions = 2

    with pytest.raises(VMError):
        vm.execute_behavior(
            agent,
            "tick",
        )


def test_instruction_counter_is_updated() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    vm.execute_behavior(
        agent,
        "tick",
    )

    assert (
        agent.context.instructions_executed
        > 0
    )


def test_event_queue_respects_max_events() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    agent.emit(
        AgentEvent("tick")
    )
    agent.emit(
        AgentEvent("tick")
    )

    with pytest.raises(VMError):
        vm.run_until_idle(
            agent,
            max_events=1,
        )


def test_unknown_event_behavior_raises() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_counter_agent()
    )

    with pytest.raises(VMError):
        vm.dispatch_event(
            agent,
            AgentEvent("unknown"),
        )


def test_agent_instances_have_independent_contexts() -> None:
    vm = VM()

    first = vm.spawn_agent(
        make_counter_agent()
    )

    second = vm.spawn_agent(
        make_counter_agent()
    )

    vm.grant_capability(
        first,
        "compute",
    )

    assert first.context.has_capability(
        "compute"
    )

    assert not second.context.has_capability(
        "compute"
    )


def test_module_agent_spawning_still_works() -> None:
    module = IRModule()

    agent_definition = make_counter_agent()

    module.add_agent(
        agent_definition
    )

    vm = VM()

    agent = vm.spawn_agent_by_name(
        module,
        "Counter",
    )

    assert agent.name == "Counter"
    assert agent.state["value"] == 0
