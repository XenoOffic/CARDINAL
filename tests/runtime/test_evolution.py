from __future__ import annotations

from dataclasses import dataclass

from runtime.vm.decision import (
    DecisionAction,
    DecisionPriority,
    RuntimeDecision,
)
from runtime.vm.evolution import (
    EvolutionEngine,
    EvolutionRequest,
    EvolutionStatus,
)
from runtime.vm.experiment import (
    Experiment,
    ExperimentCandidate,
    ExperimentEngine,
    ExperimentHypothesis,
    VerificationCriteria,
)
from sandbox.bridge import (
    SandboxExecution,
    SandboxLimits,
)


@dataclass
class FakeBridgeResult:
    success: bool
    status: str
    experiment_id: str
    candidate_id: str
    instructions_used: int
    memory_used_bytes: int
    execution_time_ms: int
    message: str


class FakeBridge:
    def __init__(
        self,
        *,
        success: bool = True,
        status: str = "passed",
    ) -> None:
        self.success = success
        self.status = status

    def execute(
        self,
        *,
        experiment_id: str,
        candidate_id: str,
        limits: SandboxLimits,
        execution: SandboxExecution,
    ) -> FakeBridgeResult:
        return FakeBridgeResult(
            success=self.success,
            status=self.status,
            experiment_id=experiment_id,
            candidate_id=candidate_id,
            instructions_used=(
                execution.instructions_used
            ),
            memory_used_bytes=(
                execution.memory_used_bytes
            ),
            execution_time_ms=(
                execution.execution_time_ms
            ),
            message="fake sandbox result",
        )


def make_experiment_engine() -> ExperimentEngine:
    engine = ExperimentEngine()

    experiment = Experiment(
        identifier="evolution-001",
        hypothesis=ExperimentHypothesis(
            statement=(
                "The candidate reduces runtime "
                "execution cost."
            ),
            rationale=(
                "A controlled optimization candidate "
                "should be evaluated in isolation."
            ),
            expected_outcome=(
                "The candidate stays within resource "
                "limits."
            ),
        ),
        candidate=ExperimentCandidate(
            identifier="candidate-001",
            description=(
                "Controlled optimization candidate."
            ),
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
            VerificationCriteria(
                name="instructions_used",
                expected=100,
                operator="<=",
            ),
            VerificationCriteria(
                name="memory_used_bytes",
                expected=1024,
                operator="<=",
            ),
            VerificationCriteria(
                name="execution_time_ms",
                expected=100,
                operator="<=",
            ),
        ),
    )

    engine.register(experiment)

    return engine


def make_decision(
    action: DecisionAction = DecisionAction.VERIFY,
) -> RuntimeDecision:
    return RuntimeDecision(
        target="behavior:test",
        action=action,
        priority=DecisionPriority.MEDIUM,
        reason="Controlled evolution test.",
        confidence=0.90,
        requires_verification=True,
    )


def make_request(
    *,
    action: DecisionAction = DecisionAction.VERIFY,
    regression_passed: bool = True,
    policy_passed: bool = True,
) -> EvolutionRequest:
    return EvolutionRequest(
        identifier="evolution-request-001",
        decision=make_decision(action),
        experiment_id="evolution-001",
        regression_passed=regression_passed,
        policy_passed=policy_passed,
    )


def make_limits() -> SandboxLimits:
    return SandboxLimits(
        max_instructions=1000,
        max_memory_bytes=4096,
        max_execution_time_ms=1000,
    )


def make_execution() -> SandboxExecution:
    return SandboxExecution(
        instructions_used=100,
        memory_used_bytes=1024,
        execution_time_ms=100,
    )


def test_evolution_approved_when_all_checks_pass():
    engine = make_experiment_engine()
    evolution = EvolutionEngine(engine)

    report = evolution.evolve(
        make_request(),
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
    )

    assert report.status == EvolutionStatus.APPROVED
    assert report.approved
    assert not report.blocked
    assert report.experiment is not None
    assert report.safety_gate is not None
    assert report.safety_gate.approved


def test_evolution_blocked_when_regression_fails():
    engine = make_experiment_engine()
    evolution = EvolutionEngine(engine)

    report = evolution.evolve(
        make_request(
            regression_passed=False
        ),
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
    )

    assert report.status == EvolutionStatus.BLOCKED
    assert report.blocked
    assert report.safety_gate is not None
    assert not report.safety_gate.approved


def test_evolution_blocked_when_policy_fails():
    engine = make_experiment_engine()
    evolution = EvolutionEngine(engine)

    report = evolution.evolve(
        make_request(
            policy_passed=False
        ),
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
    )

    assert report.status == EvolutionStatus.BLOCKED
    assert report.blocked
    assert report.safety_gate is not None
    assert not report.safety_gate.approved


def test_evolution_blocked_when_sandbox_fails():
    engine = make_experiment_engine()
    evolution = EvolutionEngine(engine)

    report = evolution.evolve(
        make_request(),
        bridge=FakeBridge(
            success=False,
            status="failed",
        ),
        limits=make_limits(),
        execution=make_execution(),
    )

    assert report.status == EvolutionStatus.BLOCKED
    assert report.blocked
    assert report.experiment is not None
    assert not report.experiment.success
    assert report.safety_gate is not None
    assert not report.safety_gate.approved


def test_ignore_decision_blocks_evolution():
    engine = make_experiment_engine()
    evolution = EvolutionEngine(engine)

    report = evolution.evolve(
        make_request(
            action=DecisionAction.IGNORE
        ),
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
    )

    assert report.status == EvolutionStatus.BLOCKED
    assert report.experiment is None
    assert report.safety_gate is None


def test_missing_experiment_fails_cleanly():
    engine = ExperimentEngine()
    evolution = EvolutionEngine(engine)

    report = evolution.evolve(
        EvolutionRequest(
            identifier="missing",
            decision=make_decision(),
            experiment_id="does-not-exist",
            regression_passed=True,
            policy_passed=True,
        ),
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
    )

    assert report.status == EvolutionStatus.FAILED
    assert report.experiment is None
    assert report.safety_gate is None


def test_evolution_requires_verification():
    engine = make_experiment_engine()
    evolution = EvolutionEngine(engine)

    decision = RuntimeDecision(
        target="behavior:test",
        action=DecisionAction.VERIFY,
        priority=DecisionPriority.MEDIUM,
        reason="Test decision.",
        confidence=0.90,
        requires_verification=False,
    )

    request = EvolutionRequest(
        identifier="no-verification",
        decision=decision,
        experiment_id="evolution-001",
        regression_passed=True,
        policy_passed=True,
    )

    report = evolution.evolve(
        request,
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
    )

    assert report.status == EvolutionStatus.BLOCKED
    assert report.experiment is None
    assert report.safety_gate is None


def test_evolution_report_preserves_decision():
    engine = make_experiment_engine()
    evolution = EvolutionEngine(engine)

    decision = make_decision(
        DecisionAction.INVESTIGATE
    )

    request = EvolutionRequest(
        identifier="preserve-decision",
        decision=decision,
        experiment_id="evolution-001",
        regression_passed=True,
        policy_passed=True,
    )

    report = evolution.evolve(
        request,
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
    )

    assert report.decision == decision
    assert report.decision.action == (
        DecisionAction.INVESTIGATE
    )


def test_evolution_is_deterministic():
    engine = make_experiment_engine()
    evolution = EvolutionEngine(engine)

    request = make_request()

    first = evolution.evolve(
        request,
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
    )

    second = evolution.evolve(
        request,
        bridge=FakeBridge(),
        limits=make_limits(),
        execution=make_execution(),
    )

    assert first.status == second.status
    assert first.reason == second.reason
    assert first.approved == second.approved
