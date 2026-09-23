from __future__ import annotations

import pytest

from compiler.ir import (
    IRBehavior,
    IRAgent,
    Instruction,
    OpCode,
)
from runtime.vm import (
    AgentEvent,
    AgentLifecycle,
    VM,
    VMError,
)


def make_agent(
    name: str,
    behavior_name: str = "message",
) -> IRAgent:
    agent = IRAgent(
        name=name,
    )

    agent.add_behavior(
        IRBehavior(
            name=behavior_name,
            instructions=[
                Instruction(
                    OpCode.RETURN
                )
            ],
        )
    )

    return agent


def test_spawn_registers_agent_with_message_bus() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_agent("A")
    )

    assert vm.get_agent("A") is agent
    assert vm.pending_messages(agent) == 0


def test_message_requires_send_capability() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B")
    )

    with pytest.raises(VMError):
        vm.send_message(
            sender,
            receiver,
            "hello",
        )


def test_message_requires_receive_capability() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B")
    )

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    vm.send_message(
        sender,
        receiver,
        "hello",
        "world",
    )

    with pytest.raises(VMError):
        vm.receive_message(receiver)


def test_agents_can_exchange_messages() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B")
    )

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    vm.grant_capability(
        receiver,
        "messaging.receive",
    )

    message = vm.send_message(
        sender,
        receiver,
        "hello",
        {"value": 42},
    )

    received = vm.receive_message(
        receiver
    )

    assert received == message
    assert received is not None
    assert received.sender == "A"
    assert received.recipient == "B"
    assert received.type == "hello"
    assert received.payload == {
        "value": 42
    }


def test_message_counters_update() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B")
    )

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    vm.grant_capability(
        receiver,
        "messaging.receive",
    )

    vm.send_message(
        sender,
        receiver,
        "hello",
    )

    vm.receive_message(
        receiver
    )

    assert sender.context.messages_sent == 1
    assert receiver.context.messages_received == 1


def test_multiple_messages_preserve_order() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B")
    )

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    vm.grant_capability(
        receiver,
        "messaging.receive",
    )

    vm.send_message(
        sender,
        receiver,
        "one",
    )

    vm.send_message(
        sender,
        receiver,
        "two",
    )

    vm.send_message(
        sender,
        receiver,
        "three",
    )

    messages = vm.receive_messages(
        receiver
    )

    assert [
        message.type
        for message in messages
    ] == [
        "one",
        "two",
        "three",
    ]


def test_message_metadata_is_preserved() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B")
    )

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    vm.grant_capability(
        receiver,
        "messaging.receive",
    )

    vm.send_message(
        sender,
        receiver,
        "hello",
        metadata={
            "priority": 10,
        },
    )

    message = vm.receive_message(
        receiver
    )

    assert message is not None
    assert message.metadata == {
        "priority": 10
    }


def test_message_history_is_recorded() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B")
    )

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    vm.send_message(
        sender,
        receiver,
        "hello",
    )

    assert len(
        vm.message_bus.history
    ) == 1


def test_message_can_be_dispatched_as_event() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B", "hello")
    )

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    vm.grant_capability(
        receiver,
        "messaging.receive",
    )

    message = vm.send_message(
        sender,
        receiver,
        "hello",
        "payload",
    )

    result = vm.dispatch_message(
        receiver,
        message,
    )

    assert result is None
    assert receiver.lifecycle == (
        AgentLifecycle.RUNNING
    )


def test_process_next_message() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B", "hello")
    )

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    vm.grant_capability(
        receiver,
        "messaging.receive",
    )

    vm.send_message(
        sender,
        receiver,
        "hello",
    )

    vm.process_next_message(
        receiver
    )

    assert vm.pending_messages(
        receiver
    ) == 0


def test_memory_is_isolated_between_agents() -> None:
    vm = VM()

    first = vm.spawn_agent(
        make_agent("A")
    )

    second = vm.spawn_agent(
        make_agent("B")
    )

    vm.remember(
        first,
        "answer",
        42,
    )

    assert vm.recall(
        first,
        "answer",
    ) == 42

    assert vm.recall(
        second,
        "answer",
    ) is None


def test_memory_can_be_forgotten() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_agent("A")
    )

    vm.remember(
        agent,
        "value",
        100,
    )

    vm.forget(
        agent,
        "value",
    )

    assert vm.recall(
        agent,
        "value",
    ) is None


def test_scheduler_registers_spawned_agents() -> None:
    vm = VM()

    vm.spawn_agent(
        make_agent("A")
    )

    vm.spawn_agent(
        make_agent("B")
    )

    assert "A" in vm.scheduler.queue
    assert "B" in vm.scheduler.queue


def test_scheduler_tick_processes_event() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_agent("A", "tick")
    )

    vm.start_agent(agent)

    vm.emit_event(
        agent,
        AgentEvent("tick"),
    )

    assert vm.tick() is True
    assert len(agent.event_queue) == 0


def test_scheduler_stops_when_idle() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_agent("A")
    )

    vm.start_agent(agent)

    assert vm.tick() is False


def test_scheduler_processes_messages() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B", "hello")
    )

    vm.start_agent(receiver)

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    vm.grant_capability(
        receiver,
        "messaging.receive",
    )

    vm.send_message(
        sender,
        receiver,
        "hello",
    )

    assert vm.run_scheduler(
        max_ticks=10
    ) >= 1

    assert vm.pending_messages(
        receiver
    ) == 0


def test_scheduler_stats_are_updated() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_agent("A", "tick")
    )

    vm.start_agent(agent)

    vm.emit_event(
        agent,
        AgentEvent("tick"),
    )

    vm.tick()

    assert vm.scheduler.stats.ticks == 1
    assert (
        vm.scheduler.stats.agents_scheduled
        == 1
    )
    assert (
        vm.scheduler.stats.events_processed
        == 1
    )


def test_stopping_agent_removes_it_from_scheduler() -> None:
    vm = VM()

    agent = vm.spawn_agent(
        make_agent("A")
    )

    assert "A" in vm.scheduler.queue

    vm.stop_agent(agent)

    assert "A" not in vm.scheduler.queue


def test_unknown_message_recipient_raises() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    with pytest.raises(VMError):
        vm.send_message(
            sender,
            "Missing",
            "hello",
        )


def test_message_bus_history_survives_receive() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B")
    )

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    vm.grant_capability(
        receiver,
        "messaging.receive",
    )

    vm.send_message(
        sender,
        receiver,
        "hello",
    )

    vm.receive_message(
        receiver
    )

    assert len(
        vm.message_bus.history
    ) == 1


def test_message_bus_pending_count() -> None:
    vm = VM()

    sender = vm.spawn_agent(
        make_agent("A")
    )

    receiver = vm.spawn_agent(
        make_agent("B")
    )

    vm.grant_capability(
        sender,
        "messaging.send",
    )

    vm.send_message(
        sender,
        receiver,
        "one",
    )

    vm.send_message(
        sender,
        receiver,
        "two",
    )

    assert vm.pending_messages(
        receiver
    ) == 2
