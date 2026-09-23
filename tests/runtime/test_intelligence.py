from runtime.vm.intelligence import (
    RuntimeIntelligence,
)
from runtime.vm.observability import (
    RuntimeHistory,
)


def make_history() -> RuntimeHistory:
    history = RuntimeHistory()

    history.record(
        "agent.spawned",
        agent="Alpha",
    )

    history.record(
        "agent.started",
        agent="Alpha",
    )

    history.record(
        "event.processed",
        agent="Alpha",
    )

    history.record(
        "behavior.started",
        agent="Alpha",
        behavior="think",
    )

    history.record(
        "behavior.completed",
        agent="Alpha",
        behavior="think",
    )

    history.record(
        "message.sent",
        agent="Alpha",
    )

    history.record(
        "message.received",
        agent="Alpha",
    )

    return history


def test_runtime_snapshot_counts_events() -> None:
    intelligence = RuntimeIntelligence(
        make_history()
    )

    snapshot = intelligence.snapshot()

    assert snapshot.total_events == 7


def test_agent_statistics() -> None:
    intelligence = RuntimeIntelligence(
        make_history()
    )

    stats = intelligence.agent_statistics(
        "Alpha"
    )

    assert stats.agent == "Alpha"
    assert stats.events == 3
    assert stats.messages_sent == 1
    assert stats.messages_received == 1
    assert stats.behaviors_started == 1
    assert stats.behaviors_completed == 1
    assert stats.errors == 0


def test_behavior_statistics() -> None:
    intelligence = RuntimeIntelligence(
        make_history()
    )

    stats = intelligence.behavior_statistics(
        "think"
    )

    assert stats.started == 1
    assert stats.completed == 1
    assert stats.errors == 0
    assert stats.success_rate == 1.0


def test_missing_agent_returns_empty_statistics() -> None:
    intelligence = RuntimeIntelligence(
        make_history()
    )

    stats = intelligence.agent_statistics(
        "Unknown"
    )

    assert stats.agent == "Unknown"
    assert stats.events == 0
    assert stats.errors == 0


def test_missing_behavior_returns_empty_statistics() -> None:
    intelligence = RuntimeIntelligence(
        make_history()
    )

    stats = intelligence.behavior_statistics(
        "unknown"
    )

    assert stats.behavior == "unknown"
    assert stats.started == 0
    assert stats.completed == 0


def test_runtime_errors_are_detected() -> None:
    history = make_history()

    history.record(
        "runtime.error",
        agent="Alpha",
        behavior="think",
        metadata={
            "error": "test failure"
        },
    )

    intelligence = RuntimeIntelligence(
        history
    )

    snapshot = intelligence.snapshot()

    assert len(snapshot.error_events) == 1
    assert (
        snapshot.error_events[0].event_type
        == "runtime.error"
    )


def test_behavior_errors_reduce_success_rate() -> None:
    history = RuntimeHistory()

    history.record(
        "behavior.started",
        agent="Alpha",
        behavior="think",
    )

    history.record(
        "runtime.error",
        agent="Alpha",
        behavior="think",
    )

    intelligence = RuntimeIntelligence(
        history
    )

    stats = intelligence.behavior_statistics(
        "think"
    )

    assert stats.started == 1
    assert stats.completed == 0
    assert stats.errors == 1
    assert stats.success_rate == 0.0


def test_recent_errors() -> None:
    history = make_history()

    for index in range(3):
        history.record(
            "runtime.error",
            agent="Alpha",
            metadata={
                "index": index
            },
        )

    intelligence = RuntimeIntelligence(
        history
    )

    errors = intelligence.recent_errors(
        limit=2
    )

    assert len(errors) == 2
    assert errors[0].metadata["index"] == 1
    assert errors[1].metadata["index"] == 2


def test_recent_errors_zero() -> None:
    intelligence = RuntimeIntelligence(
        make_history()
    )

    assert intelligence.recent_errors(
        limit=0
    ) == []


def test_patterns_detect_agent_errors() -> None:
    history = make_history()

    history.record(
        "runtime.error",
        agent="Alpha",
    )

    intelligence = RuntimeIntelligence(
        history
    )

    patterns = intelligence.detect_patterns()

    assert any(
        pattern["type"]
        == "agent.errors"
        for pattern in patterns
    )


def test_patterns_detect_behavior_instability() -> None:
    history = RuntimeHistory()

    history.record(
        "behavior.started",
        agent="Alpha",
        behavior="think",
    )

    history.record(
        "behavior.completed",
        agent="Alpha",
        behavior="think",
    )

    history.record(
        "behavior.started",
        agent="Alpha",
        behavior="think",
    )

    history.record(
        "runtime.error",
        agent="Alpha",
        behavior="think",
    )

    intelligence = RuntimeIntelligence(
        history
    )

    patterns = intelligence.detect_patterns()

    assert any(
        pattern["type"]
        == "behavior.instability"
        for pattern in patterns
    )


def test_negative_error_limit_is_rejected() -> None:
    intelligence = RuntimeIntelligence(
        make_history()
    )

    try:
        intelligence.recent_errors(
            limit=-1
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError"
    )
