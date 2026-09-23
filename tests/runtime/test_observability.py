import pytest

from runtime.vm.observability import (
    RuntimeEvent,
    RuntimeHistory,
)


def test_runtime_event_contains_structured_data() -> None:
    event = RuntimeEvent(
        event_type="agent.started",
        timestamp=123.0,
        agent="Alpha",
        metadata={"source": "test"},
    )

    assert event.event_type == "agent.started"
    assert event.timestamp == 123.0
    assert event.agent == "Alpha"
    assert event.metadata["source"] == "test"


def test_history_records_events() -> None:
    history = RuntimeHistory()

    event = history.record(
        "agent.spawned",
        agent="Alpha",
    )

    assert event.event_type == "agent.spawned"
    assert event.agent == "Alpha"
    assert len(history.events) == 1


def test_history_preserves_metadata() -> None:
    history = RuntimeHistory()

    history.record(
        "message.sent",
        agent="Alpha",
        source="Beta",
        metadata={
            "message_type": "hello",
            "priority": 2,
        },
    )

    event = history.events[0]

    assert event.source == "Beta"
    assert event.metadata["message_type"] == "hello"
    assert event.metadata["priority"] == 2


def test_history_is_bounded() -> None:
    history = RuntimeHistory(
        max_events=3
    )

    for index in range(5):
        history.record(
            "runtime.tick",
            metadata={"index": index},
        )

    assert len(history.events) == 3
    assert history.events[0].metadata["index"] == 2
    assert history.events[-1].metadata["index"] == 4


def test_history_filter_by_event_type() -> None:
    history = RuntimeHistory()

    history.record(
        "agent.started",
        agent="Alpha",
    )

    history.record(
        "message.sent",
        agent="Alpha",
    )

    history.record(
        "agent.started",
        agent="Beta",
    )

    events = history.filter(
        event_type="agent.started"
    )

    assert len(events) == 2
    assert all(
        event.event_type == "agent.started"
        for event in events
    )


def test_history_filter_by_agent() -> None:
    history = RuntimeHistory()

    history.record(
        "agent.started",
        agent="Alpha",
    )

    history.record(
        "message.sent",
        agent="Beta",
    )

    history.record(
        "event.processed",
        agent="Alpha",
    )

    events = history.filter(
        agent="Alpha"
    )

    assert len(events) == 2
    assert all(
        event.agent == "Alpha"
        for event in events
    )


def test_history_count() -> None:
    history = RuntimeHistory()

    history.record(
        "message.sent",
        agent="Alpha",
    )

    history.record(
        "message.sent",
        agent="Alpha",
    )

    history.record(
        "event.processed",
        agent="Alpha",
    )

    assert history.count(
        event_type="message.sent"
    ) == 2

    assert history.count(
        agent="Alpha"
    ) == 3


def test_history_clear() -> None:
    history = RuntimeHistory()

    history.record(
        "agent.started",
        agent="Alpha",
    )

    history.clear()

    assert history.events == []


def test_history_rejects_invalid_size() -> None:
    with pytest.raises(ValueError):
        RuntimeHistory(max_events=0)


def test_history_rejects_empty_event_type() -> None:
    history = RuntimeHistory()

    with pytest.raises(ValueError):
        history.record("")
