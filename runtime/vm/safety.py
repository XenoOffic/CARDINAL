from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SafetyCheckType(str, Enum):
    """Types of checks performed by the safety gate."""

    VERIFICATION = "verification"
    RESOURCE = "resource"
    REGRESSION = "regression"
    POLICY = "policy"


class SafetyCheckStatus(str, Enum):
    """Result of an individual safety check."""

    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class SafetyGateStatus(str, Enum):
    """Final decision of the safety gate."""

    APPROVED = "approved"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class SafetyCheck:
    """Result of one deterministic safety check."""

    check_type: SafetyCheckType
    status: SafetyCheckStatus
    description: str
    evidence: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError(
                "description cannot be empty."
            )


@dataclass(frozen=True)
class SafetyGateResult:
    """Immutable result produced by the safety gate."""

    status: SafetyGateStatus
    checks: tuple[SafetyCheck, ...]
    reason: str

    @property
    def approved(self) -> bool:
        """Return whether the candidate passed the gate."""

        return (
            self.status
            == SafetyGateStatus.APPROVED
        )

    @property
    def failed_checks(self) -> tuple[SafetyCheck, ...]:
        """Return all checks that did not pass."""

        return tuple(
            check
            for check in self.checks
            if check.status
            != SafetyCheckStatus.PASSED
        )


class SafetyGate:
    """
    Deterministic safety gate for controlled experiments.

    The gate does not execute code, modify source files,
    or approve candidates based on opaque model decisions.

    A candidate is approved only when every required check passes.
    """

    def evaluate(
        self,
        *,
        verification_passed: bool,
        resource_limits_passed: bool,
        regression_passed: bool,
        policy_passed: bool,
        evidence: dict[str, Any] | None = None,
    ) -> SafetyGateResult:
        """
        Evaluate all required safety checks.

        Every check must pass before the candidate can be approved.
        """

        shared_evidence = dict(
            evidence or {}
        )

        checks = (
            self._verification_check(
                verification_passed,
                shared_evidence,
            ),
            self._resource_check(
                resource_limits_passed,
                shared_evidence,
            ),
            self._regression_check(
                regression_passed,
                shared_evidence,
            ),
            self._policy_check(
                policy_passed,
                shared_evidence,
            ),
        )

        failed = tuple(
            check
            for check in checks
            if check.status
            != SafetyCheckStatus.PASSED
        )

        if failed:
            names = ", ".join(
                check.check_type.value
                for check in failed
            )

            return SafetyGateResult(
                status=SafetyGateStatus.BLOCKED,
                checks=checks,
                reason=(
                    "Candidate blocked because "
                    f"required checks failed: {names}."
                ),
            )

        return SafetyGateResult(
            status=SafetyGateStatus.APPROVED,
            checks=checks,
            reason=(
                "Candidate passed all required "
                "safety checks."
            ),
        )

    @staticmethod
    def _verification_check(
        passed: bool,
        evidence: dict[str, Any],
    ) -> SafetyCheck:
        return SafetyCheck(
            check_type=SafetyCheckType.VERIFICATION,
            status=(
                SafetyCheckStatus.PASSED
                if passed
                else SafetyCheckStatus.FAILED
            ),
            description=(
                "Experiment verification must pass."
            ),
            evidence=dict(evidence),
        )

    @staticmethod
    def _resource_check(
        passed: bool,
        evidence: dict[str, Any],
    ) -> SafetyCheck:
        return SafetyCheck(
            check_type=SafetyCheckType.RESOURCE,
            status=(
                SafetyCheckStatus.PASSED
                if passed
                else SafetyCheckStatus.BLOCKED
            ),
            description=(
                "Sandbox resource limits must be respected."
            ),
            evidence=dict(evidence),
        )

    @staticmethod
    def _regression_check(
        passed: bool,
        evidence: dict[str, Any],
    ) -> SafetyCheck:
        return SafetyCheck(
            check_type=SafetyCheckType.REGRESSION,
            status=(
                SafetyCheckStatus.PASSED
                if passed
                else SafetyCheckStatus.FAILED
            ),
            description=(
                "Regression checks must pass."
            ),
            evidence=dict(evidence),
        )

    @staticmethod
    def _policy_check(
        passed: bool,
        evidence: dict[str, Any],
    ) -> SafetyCheck:
        return SafetyCheck(
            check_type=SafetyCheckType.POLICY,
            status=(
                SafetyCheckStatus.PASSED
                if passed
                else SafetyCheckStatus.BLOCKED
            ),
            description=(
                "Applicable safety policies must pass."
            ),
            evidence=dict(evidence),
  )
