from pathlib import Path

import pytest

from sandbox.bridge import (
    SandboxBridge,
    SandboxExecution,
    SandboxLimits,
)


ROOT = Path(__file__).resolve().parents[2]

RUST_BINARY = (
    ROOT
    / "sandbox"
    / "rust"
    / "target"
    / "debug"
    / "cardinal-sandbox"
)


def make_limits() -> SandboxLimits:
    return SandboxLimits(
        max_instructions=1000,
        max_memory_bytes=1_000_000,
        max_execution_time_ms=5000,
    )


def make_execution() -> SandboxExecution:
    return SandboxExecution(
        instructions_used=100,
        memory_used_bytes=1024,
        execution_time_ms=50,
    )


@pytest.mark.skipif(
    not RUST_BINARY.exists(),
    reason="Rust sandbox binary has not been built.",
)
def test_bridge_success() -> None:
    bridge = SandboxBridge(
        RUST_BINARY
    )

    result = bridge.execute(
        experiment_id="exp-001",
        candidate_id="candidate-001",
        limits=make_limits(),
        execution=make_execution(),
    )

    assert result.success is True
    assert result.status == "passed"
    assert result.experiment_id == "exp-001"
    assert result.candidate_id == "candidate-001"
    assert result.instructions_used == 100
    assert result.memory_used_bytes == 1024
    assert result.execution_time_ms == 50


@pytest.mark.skipif(
    not RUST_BINARY.exists(),
    reason="Rust sandbox binary has not been built.",
)
def test_bridge_enforces_instruction_limit() -> None:
    bridge = SandboxBridge(
        RUST_BINARY
    )

    result = bridge.execute(
        experiment_id="exp-002",
        candidate_id="candidate-002",
        limits=make_limits(),
        execution=SandboxExecution(
            instructions_used=1001,
            memory_used_bytes=1024,
            execution_time_ms=50,
        ),
    )

    assert result.success is False
    assert result.status == "failed"
    assert "instruction limit" in result.message


@pytest.mark.skipif(
    not RUST_BINARY.exists(),
    reason="Rust sandbox binary has not been built.",
)
def test_bridge_enforces_memory_limit() -> None:
    bridge = SandboxBridge(
        RUST_BINARY
    )

    result = bridge.execute(
        experiment_id="exp-003",
        candidate_id="candidate-003",
        limits=make_limits(),
        execution=SandboxExecution(
            instructions_used=100,
            memory_used_bytes=1_000_001,
            execution_time_ms=50,
        ),
    )

    assert result.success is False
    assert result.status == "failed"
    assert "memory limit" in result.message


@pytest.mark.skipif(
    not RUST_BINARY.exists(),
    reason="Rust sandbox binary has not been built.",
)
def test_bridge_enforces_time_limit() -> None:
    bridge = SandboxBridge(
        RUST_BINARY
    )

    result = bridge.execute(
        experiment_id="exp-004",
        candidate_id="candidate-004",
        limits=make_limits(),
        execution=SandboxExecution(
            instructions_used=100,
            memory_used_bytes=1024,
            execution_time_ms=5001,
        ),
    )

    assert result.success is False
    assert result.status == "failed"
    assert "execution time limit" in result.message


def test_limits_reject_zero_instruction_budget() -> None:
    with pytest.raises(ValueError):
        SandboxLimits(
            max_instructions=0,
            max_memory_bytes=100,
            max_execution_time_ms=100,
        )


def test_limits_reject_zero_memory_budget() -> None:
    with pytest.raises(ValueError):
        SandboxLimits(
            max_instructions=100,
            max_memory_bytes=0,
            max_execution_time_ms=100,
        )


def test_limits_reject_zero_time_budget() -> None:
    with pytest.raises(ValueError):
        SandboxLimits(
            max_instructions=100,
            max_memory_bytes=100,
            max_execution_time_ms=0,
        )


def test_bridge_rejects_empty_experiment() -> None:
    bridge = SandboxBridge(
        "nonexistent"
    )

    with pytest.raises(ValueError):
        bridge.execute(
            experiment_id="",
            candidate_id="candidate",
            limits=make_limits(),
            execution=make_execution(),
        )


def test_bridge_rejects_empty_candidate() -> None:
    bridge = SandboxBridge(
        "nonexistent"
    )

    with pytest.raises(ValueError):
        bridge.execute(
            experiment_id="experiment",
            candidate_id="",
            limits=make_limits(),
            execution=make_execution(),
)
