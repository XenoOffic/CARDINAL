from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CandidateStatus(str, Enum):
    """Lifecycle status of an evolution candidate."""

    PROPOSED = "proposed"
    ELIGIBLE = "eligible"
    REJECTED = "rejected"


@dataclass(frozen=True)
class EvolutionCandidate:
    """
    A proposed candidate for controlled evolution.

    A candidate describes a possible change but contains no
    executable source code.
    """

    identifier: str
    description: str
    expected_benefit: float
    risk: float
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

        if not 0.0 <= self.expected_benefit <= 1.0:
            raise ValueError(
                "expected_benefit must be between 0 and 1."
            )

        if not 0.0 <= self.risk <= 1.0:
            raise ValueError(
                "risk must be between 0 and 1."
            )


@dataclass(frozen=True)
class CandidateEvaluation:
    """Deterministic evaluation of one candidate."""

    candidate: EvolutionCandidate
    score: float
    status: CandidateStatus
    reason: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                "score must be between 0 and 1."
            )


@dataclass(frozen=True)
class CandidateReport:
    """Complete evaluation report for multiple candidates."""

    evaluations: tuple[
        CandidateEvaluation, ...
    ] = field(default_factory=tuple)

    @property
    def total(self) -> int:
        return len(self.evaluations)

    @property
    def eligible(self) -> tuple[
        CandidateEvaluation, ...
    ]:
        return tuple(
            evaluation
            for evaluation in self.evaluations
            if evaluation.status
            == CandidateStatus.ELIGIBLE
        )

    @property
    def rejected(self) -> tuple[
        CandidateEvaluation, ...
    ]:
        return tuple(
            evaluation
            for evaluation in self.evaluations
            if evaluation.status
            == CandidateStatus.REJECTED
        )

    @property
    def best(self) -> CandidateEvaluation | None:
        eligible = self.eligible

        if not eligible:
            return None

        return max(
            eligible,
            key=lambda evaluation: (
                evaluation.score,
                evaluation.candidate.identifier,
            ),
        )


class CandidateEngine:
    """
    Deterministic multi-candidate evaluation engine.

    Candidates are ranked using expected benefit and risk.

    The engine does not:
        - execute candidate code
        - modify source code
        - change runtime state
        - grant capabilities
        - automatically apply candidates
    """

    def __init__(
        self,
        *,
        minimum_score: float = 0.5,
        maximum_risk: float = 0.75,
    ) -> None:
        if not 0.0 <= minimum_score <= 1.0:
            raise ValueError(
                "minimum_score must be between 0 and 1."
            )

        if not 0.0 <= maximum_risk <= 1.0:
            raise ValueError(
                "maximum_risk must be between 0 and 1."
            )

        self.minimum_score = minimum_score
        self.maximum_risk = maximum_risk

    def evaluate(
        self,
        candidates: list[EvolutionCandidate],
    ) -> CandidateReport:
        evaluations = tuple(
            self.evaluate_one(candidate)
            for candidate in candidates
        )

        return CandidateReport(
            evaluations=evaluations
        )

    def evaluate_one(
        self,
        candidate: EvolutionCandidate,
    ) -> CandidateEvaluation:
        score = self._score(candidate)

        if candidate.risk > self.maximum_risk:
            return CandidateEvaluation(
                candidate=candidate,
                score=score,
                status=CandidateStatus.REJECTED,
                reason=(
                    "Candidate risk exceeds the "
                    "configured maximum."
                ),
            )

        if score < self.minimum_score:
            return CandidateEvaluation(
                candidate=candidate,
                score=score,
                status=CandidateStatus.REJECTED,
                reason=(
                    "Candidate score is below the "
                    "configured minimum."
                ),
            )

        return CandidateEvaluation(
            candidate=candidate,
            score=score,
            status=CandidateStatus.ELIGIBLE,
            reason=(
                "Candidate satisfies the configured "
                "benefit, risk, and score thresholds."
            ),
        )

    @staticmethod
    def _score(
        candidate: EvolutionCandidate,
    ) -> float:
        """
        Calculate a deterministic benefit/risk score.

        Higher expected benefit increases the score.
        Higher risk decreases the score.
        """

        score = (
            candidate.expected_benefit
            * (1.0 - candidate.risk)
        )

        return max(
            0.0,
            min(1.0, score),
  )
