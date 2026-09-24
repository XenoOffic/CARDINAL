from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from sandbox.bridge import (
    SandboxBridge,
    SandboxBridgeResult,
    SandboxExecution,
    SandboxLimits,
)


class ExperimentStatus(str, Enum):
    """Lifecycle state of an experiment."""

    PROPOSED = "proposed"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    REJECTED = "rejected"


class VerificationStatus(str, Enum):
    """Verification result for an experiment."""

    NOT_VERIFIED = "not_verified"
    VERIFIED = "verified"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ExperimentHypothesis:
    """A testable hypothesis."""

    statement: str
    rationale: str
    expected_outcome: str

    def __post_init__(self) -> None:
        if not self.statement:
            raise ValueError(
                "statement cannot be empty."
            )

        if not self.rationale:
            raise ValueError(
                "rationale cannot be empty."
            )

        if not self.expected_outcome:
            raise ValueError(
                "expected_outcome cannot be empty."
            )


@dataclass(frozen=True)
class ExperimentCandidate:
    """Description of a proposed candidate change."""

    identifier: str
    description: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError(
                "identifier cannot be empty."
            )

        if not self.description:
            raise ValueError(
                "description cannot be empty."
            )


@dataclass(frozen=True)
class VerificationCriteria:
    """Criteria used to determine experiment success."""

    name: str
    expected: Any
    operator: str = "=="

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError(
                "name cannot be empty."
            )

        allowed = {
            "==",
            "!=",
            ">",
            ">=",
            "<",
            "<=",
        }

        if self.operator not in allowed:
            raise ValueError(
                f"Unsupported operator: {self.operator}"
            )


@dataclass(frozen=True)
class ExperimentResult:
    """Observed result from an experiment."""

    metric: str
    actual: Any
    passed: bool
    details: str = ""


@dataclass(frozen=True)
class SandboxExperimentReport:
    """Result of running an experiment through the sandbox."""

    experiment_id: str
    candidate_id: str
    sandbox_status: str
    success: bool
    message: str
    results: tuple[ExperimentResult, ...]


@dataclass
class Experiment:
    """
    Controlled experiment definition.

    An Experiment records hypotheses, candidates, sandbox results,
    and verification state.

    It does not modify source code by itself.
    """

    identifier: str
    hypothesis: ExperimentHypothesis
    candidate: ExperimentCandidate
    criteria: tuple[
        VerificationCriteria, ...
    ]
    status: ExperimentStatus = (
        ExperimentStatus.PROPOSED
    )
    verification: VerificationStatus = (
        VerificationStatus.NOT_VERIFIED
    )
    results: list[ExperimentResult] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError(
                "identifier cannot be empty."
            )

        if not self.criteria:
            raise ValueError(
                "At least one verification criterion "
                "is required."
            )

    def start(self) -> None:
        """Move a proposed experiment into execution."""

        if self.status != ExperimentStatus.PROPOSED:
            raise RuntimeError(
                "Only proposed experiments can start."
            )

        self.status = ExperimentStatus.RUNNING

    def record_result(
        self,
        result: ExperimentResult,
    ) -> None:
        """Record an observed experiment result."""

        if self.status != ExperimentStatus.RUNNING:
            raise RuntimeError(
                "Results can only be recorded while "
                "the experiment is running."
            )

        self.results.append(result)

    def verify(self) -> VerificationStatus:
        """
        Verify the experiment from its recorded results.

        Every recorded result must pass.
        """

        if self.status != ExperimentStatus.RUNNING:
            raise RuntimeError(
                "Only running experiments can be verified."
            )

        if not self.results:
            self.verification = (
                VerificationStatus.REJECTED
            )
            self.status = ExperimentStatus.FAILED
            return self.verification

        all_passed = all(
            result.passed
            for result in self.results
        )

        if all_passed:
            self.verification = (
                VerificationStatus.VERIFIED
            )
            self.status = ExperimentStatus.PASSED
        else:
            self.verification = (
                VerificationStatus.REJECTED
            )
            self.status = ExperimentStatus.FAILED

        return self.verification

    def reject(self) -> None:
        """Explicitly reject the experiment."""

        if self.status in {
            ExperimentStatus.PASSED,
            ExperimentStatus.FAILED,
        }:
            raise RuntimeError(
                "Completed experiments cannot be rejected."
            )

        self.status = ExperimentStatus.REJECTED
        self.verification = (
            VerificationStatus.REJECTED
        )


@dataclass(frozen=True)
class ExperimentReport:
    """Immutable summary of an experiment."""

    identifier: str
    status: ExperimentStatus
    verification: VerificationStatus
    passed_results: int
    failed_results: int
    total_results: int

    @property
    def success_rate(self) -> float:
        if self.total_results == 0:
            return 0.0

        return (
            self.passed_results
            / self.total_results
        )


class ExperimentEngine:
    """
    Controlled experiment manager.

    The engine manages experiment lifecycle, sandbox execution,
    and verification.

    It never modifies source code automatically.
    """

    def __init__(self) -> None:
        self._experiments: dict[
            str, Experiment
        ] = {}

    @property
    def experiments(self) -> list[Experiment]:
        """Return registered experiments."""

        return list(
            self._experiments.values()
        )

    def register(
        self,
        experiment: Experiment,
    ) -> None:
        """Register a new experiment."""

        if experiment.identifier in (
            self._experiments
        ):
            raise ValueError(
                "Experiment identifier already exists."
            )

        self._experiments[
            experiment.identifier
        ] = experiment

    def get(
        self,
        identifier: str,
    ) -> Experiment:
        """Retrieve an experiment."""

        try:
            return self._experiments[
                identifier
            ]
        except KeyError as exc:
            raise KeyError(
                f"Unknown experiment: {identifier}"
            ) from exc

    def start(
        self,
        identifier: str,
    ) -> Experiment:
        experiment = self.get(
            identifier
        )

        experiment.start()

        return experiment

    def run_in_sandbox(
        self,
        identifier: str,
        bridge: SandboxBridge,
        limits: SandboxLimits,
        execution: SandboxExecution,
    ) -> SandboxExperimentReport:
        """
        Run a controlled experiment through the Rust sandbox.

        The Rust sandbox returns measured execution information.
        Each declared verification criterion is converted into
        an ExperimentResult.

        This method does not modify source code.
        """

        experiment = self.get(
            identifier
        )

        if experiment.status == (
            ExperimentStatus.PROPOSED
        ):
            experiment.start()

        if experiment.status != (
            ExperimentStatus.RUNNING
        ):
            raise RuntimeError(
                "Only running experiments can execute "
                "in the sandbox."
            )

        sandbox_result = bridge.execute(
            experiment_id=experiment.identifier,
            candidate_id=(
                experiment.candidate.identifier
            ),
            limits=limits,
            execution=execution,
        )

        self._record_sandbox_results(
            experiment,
            sandbox_result,
        )

        if experiment.results:
            experiment.verify()

        return SandboxExperimentReport(
            experiment_id=(
                experiment.identifier
            ),
            candidate_id=(
                experiment.candidate.identifier
            ),
            sandbox_status=(
                sandbox_result.status
            ),
            success=sandbox_result.success,
            message=sandbox_result.message,
            results=tuple(
                experiment.results
            ),
        )

    def _record_sandbox_results(
        self,
        experiment: Experiment,
        sandbox_result: SandboxBridgeResult,
    ) -> None:
        """
        Convert sandbox measurements into verification results.
        """

        values: dict[str, Any] = {
            "success": sandbox_result.success,
            "status": sandbox_result.status,
            "instructions_used": (
                sandbox_result.instructions_used
            ),
            "memory_used_bytes": (
                sandbox_result.memory_used_bytes
            ),
            "execution_time_ms": (
                sandbox_result.execution_time_ms
            ),
        }

        for criterion in experiment.criteria:
            if criterion.name not in values:
                result = ExperimentResult(
                    metric=criterion.name,
                    actual=None,
                    passed=False,
                    details=(
                        "Sandbox result does not contain "
                        f"metric: {criterion.name}"
                    ),
                )

                experiment.record_result(
                    result
                )

                continue

            actual = values[
                criterion.name
            ]

            passed = self._compare(
                actual,
                criterion.expected,
                criterion.operator,
            )

            result = ExperimentResult(
                metric=criterion.name,
                actual=actual,
                passed=passed,
                details=(
                    f"expected {criterion.operator} "
                    f"{criterion.expected!r}, "
                    f"actual {actual!r}"
                ),
            )

            experiment.record_result(
                result
            )

    @staticmethod
    def _compare(
        actual: Any,
        expected: Any,
        operator: str,
    ) -> bool:
        if operator == "==":
            return actual == expected

        if operator == "!=":
            return actual != expected

        if operator == ">":
            return actual > expected

        if operator == ">=":
            return actual >= expected

        if operator == "<":
            return actual < expected

        if operator == "<=":
            return actual <= expected

        raise ValueError(
            f"Unsupported operator: {operator}"
        )

    def verify(
        self,
        identifier: str,
    ) -> VerificationStatus:
        experiment = self.get(
            identifier
        )

        return experiment.verify()

    def reject(
        self,
        identifier: str,
    ) -> None:
        self.get(identifier).reject()

    def report(
        self,
        identifier: str,
    ) -> ExperimentReport:
        experiment = self.get(
            identifier
        )

        passed = sum(
            result.passed
            for result in experiment.results
        )

        failed = (
            len(experiment.results)
            - passed
        )

        return ExperimentReport(
            identifier=experiment.identifier,
            status=experiment.status,
            verification=(
                experiment.verification
            ),
            passed_results=passed,
            failed_results=failed,
            total_results=len(
                experiment.results
            ),
    )
