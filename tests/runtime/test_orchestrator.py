import pytest

from runtime.vm.candidates import (
    CandidateEngine,
    EvolutionCandidate,
)
from runtime.vm.decision import (
    DecisionAction,
    DecisionPriority,
    RuntimeDecision,
)
from runtime.vm.evolution import (
    EvolutionEngine,
    EvolutionStatus,
)
from runtime.vm.experiment import (
    ExperimentEngine,
    ExperimentCandidate,
    ExperimentHypothesis,
    VerificationCriteria,
)
from runtime.vm.orchestrator import (
    EvolutionOrchestrator,
    OrchestrationCandidate,
    OrchestrationStatus,
)
from runtime.vm.safety import SafetyGate
from sandbox.bridge import (
    SandboxExecution,
    SandboxLimits,
)


class FakeBridge:
    def __init__(
        self,
        *,
        success: bool = True,
        status: str = "passed",
    ) -> None:
        self.success = success
        self.status = status
        self.calls = 0

    def execute(
        self,
        *,
        experiment_id,
        candidate_id,
        limits,
        execution,
    ):
        self.calls += 1

        from sandbox.bridge import SandboxBridgeResult

        return SandboxBridgeResult(
            success=self.success,
            status=self.status,
            experiment_id=experiment_id,
            candidate_id=candidate_id,
            instructions_used=10,
            memory_used_bytes=1024,
            execution_time_ms=5,
            message="fake sandbox result",
        )


def make_decision() -> RuntimeDecision:
    return RuntimeDecision(
        target="behavior:test",
        action=DecisionAction.INVESTIGATE,
        priority=DecisionPriority.HIGH,
        reason="Test anomaly requires investigation.",
        confidence=0.95,
        requires_verification=True,
    )


def make_candidate(
    identifier: str,
    *,
    benefit: float = 0.9,
    risk: float = 0.1,
) -> OrchestrationCandidate:
    return OrchestrationCandidate(
        candidate=EvolutionCandidate(
            identifier=identifier,
            description=f"Candidate {identifier}",
            expected_benefit=benefit,
            risk=risk,
        ),
        experiment_id=f"experiment-{identifier}",
        experiment_candidate=ExperimentCandidate(
            identifier=f"experiment-candidate-{identifier}",
            description=f"Experiment candidate {identifier}",
        ),
        hypothesis=ExperimentHypothesis(
            statement=(
                f"Candidate {identifier} improves runtime."
            ),
            rationale="Controlled test.",
            expected_outcome="Sandbox passes.",
        ),
        criteria=(
            VerificationCriteria(
                name="success",
                expected=True,
                operator="==",
            ),
            VerificationCriteria(
                name="status",
                expected="passed",
                operator="==",
            ),
        ),
    )


def make_orchestrator() -> EvolutionOrchestrator:
    experiment_engine = ExperimentEngine()

    evolution_engine = EvolutionEngine(
        experiment_engine,
        SafetyGate(),
    )

    return EvolutionOrchestrator(
        candidate_engine=CandidateEngine(),
        experiment_engine=experiment_engine,
        evolution_engine=evolution_engine,
    )


def make_limits() -> SandboxLimits:
    return SandboxLimits(
        max_instructions=100,
        max_memory_bytes=4096,
        max_execution_time_ms=100,
    )


def make_execution() -> SandboxExecution:
    return SandboxExecution(
        instructions_used=10,
        memory_used_bytes=1024,
        execution_time_ms=5,
    )


def test_orchestrator_evaluates_multiple_candidates() -> None:
    orchestrator = make_orchestrator()

    report = orchestrator.orchestrate(
        identifier="evolution-1",
        decision=make_decision(),
        candidates=[
            make_candidate("a"),
            make_candidate(
                "b",
                benefit=0.3,
                risk=0.9,
            ),
        ],
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
        regression_passed=True,
        policy_passed=True,
    )

    assert report.status == (
        OrchestrationStatus.COMPLETED
    )
    assert report.total_candidates == 2
    assert len(report.eligible_candidates) == 1

    rejected = [
        result
        for result in report.candidates
        if result.evolution is None
    ]

    assert len(rejected) == 1
    assert (
        rejected[0].evaluation.candidate.identifier
        == "b"
    )


def test_eligible_candidate_reaches_safety_gate() -> None:
    bridge = FakeBridge()
    orchestrator = make_orchestrator()

    report = orchestrator.orchestrate(
        identifier="evolution-2",
        decision=make_decision(),
        candidates=[
            make_candidate("a"),
        ],
        bridge=bridge,
        limits=make_limits(),
        execution=make_execution(),
        regression_passed=True,
        policy_passed=True,
    )

    assert bridge.calls == 1
    assert len(report.approved_candidates) == 1

    evolution = (
        report.approved_candidates[0].evolution
    )

    assert evolution is not None
    assert evolution.status == EvolutionStatus.APPROVED
    assert evolution.safety_gate is not None
    assert evolution.safety_gate.approved


def test_failed_regression_blocks_candidate() -> None:
    orchestrator = make_orchestrator()

    report = orchestrator.orchestrate(
        identifier="evolution-3",
        decision=make_decision(),
        candidates=[
            make_candidate("a"),
        ],
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
        regression_passed=False,
        policy_passed=True,
    )

    assert len(report.approved_candidates) == 0
    assert len(report.blocked_candidates) == 1

    evolution = (
        report.blocked_candidates[0].evolution
    )

    assert evolution is not None
    assert evolution.status == EvolutionStatus.BLOCKED


def test_failed_policy_blocks_candidate() -> None:
    orchestrator = make_orchestrator()

    report = orchestrator.orchestrate(
        identifier="evolution-4",
        decision=make_decision(),
        candidates=[
            make_candidate("a"),
        ],
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
        regression_passed=True,
        policy_passed=False,
    )

    assert len(report.approved_candidates) == 0
    assert len(report.blocked_candidates) == 1


def test_failed_sandbox_blocks_candidate() -> None:
    orchestrator = make_orchestrator()

    report = orchestrator.orchestrate(
        identifier="evolution-5",
        decision=make_decision(),
        candidates=[
            make_candidate("a"),
        ],
        bridge=FakeBridge(
            success=False,
            status="failed",
        ),
        limits=make_limits(),
        execution=make_execution(),
        regression_passed=True,
        policy_passed=True,
    )

    assert len(report.approved_candidates) == 0
    assert len(report.blocked_candidates) == 1


def test_rejected_candidate_never_reaches_sandbox() -> None:
    bridge = FakeBridge()
    orchestrator = make_orchestrator()

    report = orchestrator.orchestrate(
        identifier="evolution-6",
        decision=make_decision(),
        candidates=[
            make_candidate(
                "dangerous",
                benefit=1.0,
                risk=0.99,
            ),
        ],
        bridge=bridge,
        limits=make_limits(),
        execution=make_execution(),
        regression_passed=True,
        policy_passed=True,
    )

    assert report.total_candidates == 1
    assert len(report.eligible_candidates) == 0
    assert len(report.blocked_candidates) == 0
    assert bridge.calls == 0

    rejected = [
        result
        for result in report.candidates
        if result.evolution is None
    ]

    assert len(rejected) == 1


def test_empty_candidates_fail_cleanly() -> None:
    orchestrator = make_orchestrator()

    report = orchestrator.orchestrate(
        identifier="evolution-empty",
        decision=make_decision(),
        candidates=[],
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
        regression_passed=True,
        policy_passed=True,
    )

    assert report.status == OrchestrationStatus.FAILED
    assert report.total_candidates == 0


def test_missing_verification_requirement_fails() -> None:
    orchestrator = make_orchestrator()

    decision = RuntimeDecision(
        target="runtime",
        action=DecisionAction.MONITOR,
        priority=DecisionPriority.MEDIUM,
        reason="Monitoring only.",
        confidence=0.8,
        requires_verification=False,
    )

    report = orchestrator.orchestrate(
        identifier="evolution-no-verify",
        decision=decision,
        candidates=[
            make_candidate("a"),
        ],
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
        regression_passed=True,
        policy_passed=True,
    )

    assert report.status == OrchestrationStatus.FAILED
    assert report.total_candidates == 0


def test_empty_identifier_is_rejected() -> None:
    orchestrator = make_orchestrator()

    with pytest.raises(ValueError):
        orchestrator.orchestrate(
            identifier="",
            decision=make_decision(),
            candidates=[
                make_candidate("a"),
            ],
            bridge=FakeBridge(),
            limits=make_limits(),
            execution=make_execution(),
            regression_passed=True,
            policy_passed=True,
        )


def test_existing_experiment_is_reused() -> None:
    experiment_engine = ExperimentEngine()

    evolution_engine = EvolutionEngine(
        experiment_engine,
        SafetyGate(),
    )

    candidate = make_candidate("existing")

    from runtime.vm.experiment import Experiment

    experiment_engine.register(
        Experiment(
            identifier=candidate.experiment_id,
            hypothesis=candidate.hypothesis,
            candidate=candidate.experiment_candidate,
            criteria=candidate.criteria,
        )
    )

    orchestrator = EvolutionOrchestrator(
        candidate_engine=CandidateEngine(),
        experiment_engine=experiment_engine,
        evolution_engine=evolution_engine,
    )

    bridge = FakeBridge()

    report = orchestrator.orchestrate(
        identifier="evolution-existing",
        decision=make_decision(),
        candidates=[candidate],
        bridge=bridge,
        limits=make_limits(),
        execution=make_execution(),
        regression_passed=True,
        policy_passed=True,
    )

    assert len(report.approved_candidates) == 1
    assert bridge.calls == 1
    assert len(experiment_engine.experiments) == 1


def test_multiple_eligible_candidates_are_independently_evaluated() -> None:
    orchestrator = make_orchestrator()
    bridge = FakeBridge()

    report = orchestrator.orchestrate(
        identifier="evolution-multiple",
        decision=make_decision(),
        candidates=[
            make_candidate(
                "a",
                benefit=0.95,
                risk=0.05,
            ),
            make_candidate(
                "b",
                benefit=0.85,
                risk=0.10,
            ),
        ],
        bridge=bridge,
        limits=make_limits(),
        execution=make_execution(),
        regression_passed=True,
        policy_passed=True,
    )

    assert report.total_candidates == 2
    assert len(report.eligible_candidates) == 2
    assert len(report.approved_candidates) == 2
    assert bridge.calls == 2


def test_orchestration_does_not_apply_candidate() -> None:
    orchestrator = make_orchestrator()

    candidate = make_candidate("safe")

    report = orchestrator.orchestrate(
        identifier="evolution-no-apply",
        decision=make_decision(),
        candidates=[candidate],
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
        regression_passed=True,
        policy_passed=True,
    )

    assert report.approved_candidates
    assert candidate.candidate.metadata == {}


def test_orchestration_is_deterministic() -> None:
    def run_once():
        orchestrator = make_orchestrator()

        return orchestrator.orchestrate(
            identifier="deterministic",
            decision=make_decision(),
            candidates=[
                make_candidate(
                    "a",
                    benefit=0.9,
                    risk=0.1,
                ),
                make_candidate(
                    "b",
                    benefit=0.8,
                    risk=0.2,
                ),
            ],
            bridge=FakeBridge(),
            limits=make_limits(),
            execution=make_execution(),
            regression_passed=True,
            policy_passed=True,
        )

    first = run_once()
    second = run_once()

    assert [
        result.evaluation.score
        for result in first.candidates
    ] == [
        result.evaluation.score
        for result in second.candidates
    ]

    assert [
        result.evolution.status
        if result.evolution is not None
        else None
        for result in first.candidates
    ] == [
        result.evolution.status
        if result.evolution is not None
        else None
        for result in second.candidates
    ]
