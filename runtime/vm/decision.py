from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .analysis import RuntimeAnomaly


class DecisionAction(str, Enum):
    """Actions that the decision engine may recommend."""

    INVESTIGATE = "investigate"
    MONITOR = "monitor"
    VERIFY = "verify"
    IGNORE = "ignore"


class DecisionPriority(str, Enum):
    """Priority assigned to a runtime decision."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class DecisionEvidence:
    """Evidence supporting a runtime decision."""

    source: str
    value: Any
    description: str


@dataclass(frozen=True)
class RuntimeDecision:
    """A structured, non-executing runtime decision."""

    target: str
    action: DecisionAction
    priority: DecisionPriority
    reason: str
    confidence: float
    evidence: tuple[DecisionEvidence, ...] = field(
        default_factory=tuple
    )
    requires_verification: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not self.target:
            raise ValueError(
                "target cannot be empty."
            )

        if not self.reason:
            raise ValueError(
                "reason cannot be empty."
            )


@dataclass(frozen=True)
class DecisionReport:
    """Complete output of the decision engine."""

    decisions: tuple[RuntimeDecision, ...] = field(
        default_factory=tuple
    )

    @property
    def count(self) -> int:
        return len(self.decisions)

    def by_priority(
        self,
        priority: DecisionPriority,
    ) -> list[RuntimeDecision]:
        return [
            decision
            for decision in self.decisions
            if decision.priority == priority
        ]


class DecisionEngine:
    """
    Deterministic decision layer for CARDINAL.

    The engine converts runtime anomalies into structured
    recommendations. It never executes the recommendations,
    modifies source code, changes agent state, or grants
    capabilities.
    """

    def __init__(
        self,
        *,
        minimum_confidence: float = 0.5,
    ) -> None:
        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError(
                "minimum_confidence must be between 0 and 1."
            )

        self.minimum_confidence = (
            minimum_confidence
        )

    def decide(
        self,
        anomalies: list[RuntimeAnomaly],
    ) -> DecisionReport:
        decisions: list[RuntimeDecision] = []

        for anomaly in anomalies:
            decision = self._decide_anomaly(
                anomaly
            )

            if (
                decision.confidence
                >= self.minimum_confidence
            ):
                decisions.append(decision)

        return DecisionReport(
            decisions=tuple(decisions)
        )

    def decide_one(
        self,
        anomaly: RuntimeAnomaly,
    ) -> RuntimeDecision | None:
        decision = self._decide_anomaly(
            anomaly
        )

        if (
            decision.confidence
            < self.minimum_confidence
        ):
            return None

        return decision

    def _decide_anomaly(
        self,
        anomaly: RuntimeAnomaly,
    ) -> RuntimeDecision:
        target = self._target_for(
            anomaly
        )

        evidence = (
            DecisionEvidence(
                source=anomaly.anomaly_type,
                value=anomaly.value,
                description=anomaly.description,
            ),
        )

        if anomaly.anomaly_type == (
            "high_error_rate"
        ):
            return RuntimeDecision(
                target=target,
                action=DecisionAction.INVESTIGATE,
                priority=(
                    DecisionPriority.HIGH
                ),
                reason=(
                    "Repeated runtime failures "
                    "were detected."
                ),
                confidence=0.95,
                evidence=evidence,
                requires_verification=True,
            )

        if anomaly.anomaly_type == (
            "slow_behavior"
        ):
            return RuntimeDecision(
                target=target,
                action=DecisionAction.MONITOR,
                priority=(
                    DecisionPriority.MEDIUM
                ),
                reason=(
                    "Elevated execution duration "
                    "was detected."
                ),
                confidence=0.85,
                evidence=evidence,
                requires_verification=True,
            )

        return RuntimeDecision(
            target=target,
            action=DecisionAction.VERIFY,
            priority=DecisionPriority.LOW,
            reason=(
                "An unclassified runtime anomaly "
                "requires verification."
            ),
            confidence=0.60,
            evidence=evidence,
            requires_verification=True,
        )

    @staticmethod
    def _target_for(
        anomaly: RuntimeAnomaly,
    ) -> str:
        if anomaly.behavior is not None:
            return (
                f"behavior:{anomaly.behavior}"
            )

        if anomaly.agent is not None:
            return (
                f"agent:{anomaly.agent}"
            )

        return "runtime"
