from runtime.vm.intelligence import (
    AgentStatistics,
    BehaviorStatistics,
    RuntimeSnapshot,
)
from runtime.vm.vm import VM


def test_vm_exposes_runtime_intelligence() -> None:
    vm = VM()

    assert vm.intelligence.history is (
        vm.observability
    )


def test_vm_runtime_snapshot_is_live() -> None:
    vm = VM()

    vm.observability.record(
        "agent.spawned",
        agent="Alpha",
    )

    snapshot = vm.runtime_snapshot()

    assert isinstance(
        snapshot,
        RuntimeSnapshot,
    )

    assert snapshot.total_events == 1


def test_vm_agent_statistics() -> None:
    vm = VM()

    vm.observability.record(
        "agent.started",
        agent="Alpha",
    )

    vm.observability.record(
        "event.processed",
        agent="Alpha",
    )

    stats = vm.agent_statistics(
        "Alpha"
    )

    assert isinstance(
        stats,
        AgentStatistics,
    )

    assert stats.agent == "Alpha"
    assert stats.events == 2


def test_vm_behavior_statistics() -> None:
    vm = VM()

    vm.observability.record(
        "behavior.started",
        agent="Alpha",
        behavior="think",
    )

    vm.observability.record(
        "behavior.completed",
        agent="Alpha",
        behavior="think",
    )

    stats = vm.behavior_statistics(
        "think"
    )

    assert isinstance(
        stats,
        BehaviorStatistics,
    )

    assert stats.started == 1
    assert stats.completed == 1
    assert stats.success_rate == 1.0


def test_vm_recent_errors() -> None:
    vm = VM()

    vm.observability.record(
        "runtime.error",
        agent="Alpha",
        behavior="think",
        metadata={
            "error": "failure"
        },
    )

    errors = vm.recent_errors()

    assert len(errors) == 1
    assert errors[0].event_type == (
        "runtime.error"
    )


def test_vm_detect_runtime_patterns() -> None:
    vm = VM()

    vm.observability.record(
        "runtime.error",
        agent="Alpha",
    )

    patterns = vm.detect_runtime_patterns()

    assert any(
        pattern["type"] == "agent.errors"
        for pattern in patterns
    )
