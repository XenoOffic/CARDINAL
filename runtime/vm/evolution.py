from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .decision import (
    DecisionAction,
    RuntimeDecision,
)
from .experiment import (
    ExperimentEngine,
    SandboxExperimentReport,
)
from .safety import (
    SafetyGate,
    SafetyGateResult,
)


class EvolutionStatus(str, Enum):
    """Lifecycle status of a controlled evolution attempt."""

    PROPOSED = "proposed"
    RUNNING = "running"
    APPROVED = "approved"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True)
class EvolutionRequest:
    """
    Explicit request to evaluate a candidate evolution.

    The request contains a decision and an already-defined
    experiment. It never contains executable source code.
    """

    identifier: str
    decision: RuntimeDecision
    experiment_id: str
    regression_passed: bool
    policy_passed: bool

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError(
                "identifier cannot be empty."
            )

        if not self.experiment_id:
            raise ValueError(
                "experiment_id cannot be empty."
            )


@dataclass(frozen=True)
class EvolutionReport:
    """Complete result of a controlled evolution attempt."""

    identifier: str
    status: EvolutionStatus
    decision: RuntimeDecision
    experiment: SandboxExperimentReport | None
    safety_gate: SafetyGateResult | None
    reason: str

    @property
    def approved(self) -> bool:
        return self.status == EvolutionStatus.APPROVED

    @property
    def blocked(self) -> bool:
        return self.status == EvolutionStatus.BLOCKED


class EvolutionEngine:
    """
    Controlled evolution orchestrator for CARDINAL.

    The engine coordinates:

        Decision
          ↓
        Experiment
          ↓
        Sandbox
          ↓
        Verification
          ↓
        Safety Gate
          ↓
        APPROVED / BLOCKED

    It does not modify source code, execute arbitrary source,
    grant capabilities, or change runtime state automatically.
    """

    def __init__(
        self,
        experiment_engine: ExperimentEngine,
        safety_gate: SafetyGate | None = None,
    ) -> None:
        self.experiment_engine = experiment_engine
        self.safety_gate = (
            safety_gate
            if safety_gate is not None
            else SafetyGate()
        )

    def evolve(
        self,
        request: EvolutionRequest,
        *,
        bridge,
        limits,
        execution,
    ) -> EvolutionReport:
        """
        Execute one controlled evolution evaluation.

        The caller explicitly provides the sandbox bridge,
        resource limits, execution measurements, regression
        result, and policy result.
        """

        if request.decision.action == DecisionAction.IGNORE:
            return EvolutionReport(
                identifier=request.identifier,
                status=EvolutionStatus.BLOCKED,
                decision=request.decision,
                experiment=None,
                safety_gate=None,
                reason=(
                    "Evolution was blocked because the "
                    "decision action is IGNORE."
                ),
            )

        if not request.decision.requires_verification:
            return EvolutionReport(
                identifier=request.identifier,
                status=EvolutionStatus.BLOCKED,
                decision=request.decision,
                experiment=None,
                safety_gate=None,
                reason=(
                    "Evolution requires explicit "
                    "verification."
                ),
            )

        experiment = self.experiment_engine.get(
            request.experiment_id
        )

        if experiment is None:
            return EvolutionReport(
                identifier=request.identifier,
                status=EvolutionStatus.FAILED,
                decision=request.decision,
                experiment=None,
                safety_gate=None,
                reason=(
                    "The requested experiment "
                    "does not exist."
                ),
            )

        try:
            sandbox_report = (
                self.experiment_engine.run_in_sandbox(
                    request.experiment_id,
                    bridge,
                    limits,
                    execution,
                )
            )
        except Exception as exc:
            return EvolutionReport(
                identifier=request.identifier,
                status=EvolutionStatus.FAILED,
                decision=request.decision,
                experiment=None,
                safety_gate=None,
                reason=(
                    "Evolution execution failed: "
                    f"{exc}"
                ),
            )

        verification_passed = sandbox_report.success

        resource_limits_passed = (
            sandbox_report.sandbox_status == "passed"
        )

        safety_result = self.safety_gate.evaluate(
            verification_passed=verification_passed,
            resource_limits_passed=(
                resource_limits_passed
            ),
            regression_passed=(
                request.regression_passed
            ),
            policy_passed=request.policy_passed,
            evidence={
                "decision_target": (
                    request.decision.target
                ),
                "decision_action": (
                    request.decision.action.value
                ),
                "decision_confidence": (
                    request.decision.confidence
                ),
                "experiment_id": (
                    request.experiment_id
                ),
                "sandbox_status": (
                    sandbox_report.sandbox_status
                ),
            },
        )

        if safety_result.approved:
            return EvolutionReport(
                identifier=request.identifier,
                status=EvolutionStatus.APPROVED,
                decision=request.decision,
                experiment=sandbox_report,
                safety_gate=safety_result,
                reason=(
                    "Evolution candidate passed "
                    "verification, resource, regression, "
                    "and policy checks."
                ),
            )

        return EvolutionReport(
            identifier=request.identifier,
            status=EvolutionStatus.BLOCKED,
            decision=request.decision,
            experiment=sandbox_report,
            safety_gate=safety_result,
            reason=(
                "Evolution candidate was blocked "
                "by the safety gate."
            ),
        )

    @staticmethod
    def experiment_for(
        experiment_engine: ExperimentEngine,
        experiment_id: str,
    ):
        """Return a registered experiment if it exists."""

        return experiment_engine.get(
            experiment_id
    )
