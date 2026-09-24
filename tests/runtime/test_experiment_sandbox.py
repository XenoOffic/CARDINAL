from pathlib import Path

import pytest

from runtime.vm.experiment import (
    Experiment,
    ExperimentCandidate,
    ExperimentEngine,
    ExperimentHypothesis,
    ExperimentStatus,
    VerificationCriteria,
    VerificationStatus,
)
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


def make_experiment() -> Experiment:
    return Experiment(
        identifier="experiment-001",
        hypothesis=ExperimentHypothesis(
            statement=(
                "The candidate remains within "
                "sandbox resource limits."
            ),
            rationale=(
                "Controlled resource usage should "
                "allow verification."
            ),
            expected_outcome=(
                "All sandbox criteria pass."
            ),
        ),
        candidate=ExperimentCandidate(
            identifier="candidate-001",
            description=(
                "Controlled candidate experiment."
            ),
        ),
        criteria=(
            VerificationCriteria(
                name="success",
                expected=True,
            ),
            VerificationCriteria(
                name="status",
                expected="passed",
            ),
            VerificationCriteria(
                name="instructions_used",
                expected=100,
                operator="<=",
            ),
            VerificationCriteria(
                name="memory_used_bytes",
                expected=1_000_000,
                operator="<=",
            ),
            VerificationCriteria(
                name="execution_time_ms",
                expected=5000,
                operator="<=",
            ),
        ),
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
def test_experiment_runs_through_rust_sandbox() -> None:
    engine = ExperimentEngine()

    experiment = make_experiment()

    engine.register(experiment)

    bridge = SandboxBridge(
        RUST_BINARY
    )

    result = engine.run_in_sandbox(
        "experiment-001",
        bridge,
        make_limits(),
        make_execution(),
    )

    assert result.success is True
    assert result.sandbox_status == "passed"

    assert (
        experiment.status
        == ExperimentStatus.PASSED
    )

    assert (
        experiment.verification
        == VerificationStatus.VERIFIED
    )

    assert len(
        experiment.results
    ) == 5

    assert all(
        result.passed
        for result in experiment.results
    )


@pytest.mark.skipif(
    not RUST_BINARY.exists(),
    reason="Rust sandbox binary has not been built.",
)
def test_failed_sandbox_verification_fails_experiment() -> None:
    engine = ExperimentEngine()

    experiment = make_experiment()

    engine.register(experiment)

    bridge = SandboxBridge(
        RUST_BINARY
    )

    result = engine.run_in_sandbox(
        "experiment-001",
        bridge,
        make_limits(),
        SandboxExecution(
            instructions_used=1001,
            memory_used_bytes=1024,
            execution_time_ms=50,
        ),
    )

    assert result.success is False

    assert (
        experiment.status
        == ExperimentStatus.FAILED
    )

    assert (
        experiment.verification
        == VerificationStatus.REJECTED
    )

    assert any(
        not item.passed
        for item in experiment.results
    )


def test_experiment_requires_criteria() -> None:
    with pytest.raises(ValueError):
        Experiment(
            identifier="experiment-invalid",
            hypothesis=ExperimentHypothesis(
                statement="test",
                rationale="test",
                expected_outcome="test",
            ),
            candidate=ExperimentCandidate(
                identifier="candidate",
                description="test",
            ),
            criteria=(),
  )
