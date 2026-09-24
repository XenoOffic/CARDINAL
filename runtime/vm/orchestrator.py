from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .candidates import (
    CandidateEvaluation,
    CandidateEngine,
    EvolutionCandidate,
)
from .decision import RuntimeDecision
from .evolution import (
    EvolutionEngine,
    EvolutionReport,
    EvolutionRequest,
)
from .experiment import (
    ExperimentEngine,
    ExperimentCandidate,
    ExperimentHypothesis,
    VerificationCriteria,
)


class OrchestrationStatus(str, Enum):
    """Status of one complete evolution orchestration."""

    PROPOSED = "proposed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class OrchestrationCandidate:
    """
    Candidate together with the experiment required to evaluate it.
    """

    candidate: EvolutionCandidate
    experiment_id: str
    experiment_candidate: ExperimentCandidate
    hypothesis: ExperimentHypothesis
    criteria: tuple[VerificationCriteria, ...]

    def __post_init__(self) -> None:
        if not self.experiment_id:
            raise ValueError(
                "experiment_id cannot be empty."
            )

        if not self.criteria:
            raise ValueError(
                "At least one verification criterion "
                "is required."
            )


@dataclass(frozen=True)
class CandidateOrchestrationResult:
    """Result of evaluating one candidate."""

    evaluation: CandidateEvaluation
    evolution: EvolutionReport | None


@dataclass(frozen=True)
class OrchestrationReport:
    """Complete result of a multi-candidate evolution run."""

    identifier: str
    status: OrchestrationStatus
    decision: RuntimeDecision
    candidates: tuple[
        CandidateOrchestrationResult, ...
    ]
    reason: str

    @property
    def total_candidates(self) -> int:
        return len(self.candidates)

    @property
    def eligible_candidates(self) -> tuple[
        CandidateOrchestrationResult, ...
    ]:
        return tuple(
            result
            for result in self.candidates
            if result.evaluation.status.value == "eligible"
        )

    @property
    def approved_candidates(self) -> tuple[
        CandidateOrchestrationResult, ...
    ]:
        return tuple(
            result
            for result in self.candidates
            if (
                result.evolution is not None
                and result.evolution.approved
            )
        )

    @property
    def blocked_candidates(self) -> tuple[
        CandidateOrchestrationResult, ...
    ]:
        return tuple(
            result
            for result in self.candidates
            if (
                result.evolution is not None
                and result.evolution.blocked
            )
        )


class EvolutionOrchestrator:
    """
    End-to-end controlled evolution orchestrator.

    The orchestrator connects:

        Decision
          ↓
        Candidate Engine
          ↓
        Experiment Engine
          ↓
        Rust Sandbox
          ↓
        Verification
          ↓
        Safety Gate

    It never:
        - modifies source code
        - executes arbitrary source code
        - grants capabilities
        - changes runtime state automatically
        - applies an approved candidate automatically
    """

    def __init__(
        self,
        *,
        candidate_engine: CandidateEngine,
        experiment_engine: ExperimentEngine,
        evolution_engine: EvolutionEngine,
    ) -> None:
        self.candidate_engine = candidate_engine
        self.experiment_engine = experiment_engine
        self.evolution_engine = evolution_engine

    def orchestrate(
        self,
        *,
        identifier: str,
        decision: RuntimeDecision,
        candidates: list[OrchestrationCandidate],
        bridge: Any,
        limits: Any,
        execution: Any,
        regression_passed: bool,
        policy_passed: bool,
    ) -> OrchestrationReport:
        """
        Execute one complete controlled evolution cycle.
        """

        if not identifier:
            raise ValueError(
                "identifier cannot be empty."
            )

        if not candidates:
            return OrchestrationReport(
                identifier=identifier,
                status=OrchestrationStatus.FAILED,
                decision=decision,
                candidates=(),
                reason=(
                    "No evolution candidates were provided."
                ),
            )

        if not decision.requires_verification:
            return OrchestrationReport(
                identifier=identifier,
                status=OrchestrationStatus.FAILED,
                decision=decision,
                candidates=(),
                reason=(
                    "Evolution requires explicit "
                    "verification."
                ),
            )

        candidate_definitions = [
            item.candidate
            for item in candidates
        ]

        evaluations = self.candidate_engine.evaluate(
            candidate_definitions
        )

        candidate_map = {
            item.candidate.identifier: item
            for item in candidates
        }

        results: list[CandidateOrchestrationResult] = []

        for evaluation in evaluations.evaluations:
            candidate_definition = candidate_map[
                evaluation.candidate.identifier
            ]

            if evaluation.status.value != "eligible":
                results.append(
                    CandidateOrchestrationResult(
                        evaluation=evaluation,
                        evolution=None,
                    )
                )
                continue

            if (
                candidate_definition.experiment_id
                in self.experiment_engine.experiments
            ):
                pass

            experiment = self._ensure_experiment(
                candidate_definition
            )

            request = EvolutionRequest(
                identifier=(
                    f"{identifier}:"
                    f"{evaluation.candidate.identifier}"
                ),
                decision=decision,
                experiment_id=experiment.identifier,
                regression_passed=regression_passed,
                policy_passed=policy_passed,
            )

            evolution_report = (
                self.evolution_engine.evolve(
                    request,
                    bridge=bridge,
                    limits=limits,
                    execution=execution,
                )
            )

            results.append(
                CandidateOrchestrationResult(
                    evaluation=evaluation,
                    evolution=evolution_report,
                )
            )
    def orchestrate(
        self,
        *,
        identifier: str,
        decision: RuntimeDecision,
        candidates: list[OrchestrationCandidate],
        bridge: Any,
        limits: Any,
        execution: Any,
        regression_passed: bool,
        policy_passed: bool,
    ) -> OrchestrationReport:
        """
        Execute one complete controlled evolution cycle.
        """

        if not identifier:
            raise ValueError(
                "identifier cannot be empty."
            )

        if not candidates:
            return OrchestrationReport(
                identifier=identifier,
                status=OrchestrationStatus.FAILED,
                decision=decision,
                candidates=(),
                reason=(
                    "No evolution candidates were provided."
                ),
            )

        if not decision.requires_verification:
            return OrchestrationReport(
                identifier=identifier,
                status=OrchestrationStatus.FAILED,
                decision=decision,
                candidates=(),
                reason=(
                    "Evolution requires explicit "
                    "verification."
                ),
            )

        candidate_definitions = [
            item.candidate
            for item in candidates
        ]

        evaluations = self.candidate_engine.evaluate(
            candidate_definitions
        )

        candidate_map = {
            item.candidate.identifier: item
            for item in candidates
        }

        results: list[CandidateOrchestrationResult] = []

        for evaluation in evaluations.evaluations:
            candidate_definition = candidate_map[
                evaluation.candidate.identifier
            ]

            if evaluation.status.value != "eligible":
                results.append(
                    CandidateOrchestrationResult(
                        evaluation=evaluation,
                        evolution=None,
                    )
                )
                continue

            experiment = self._ensure_experiment(
                candidate_definition
            )

            request = EvolutionRequest(
                identifier=(
                    f"{identifier}:"
                    f"{evaluation.candidate.identifier}"
                ),
                decision=decision,
                experiment_id=experiment.identifier,
                regression_passed=regression_passed,
                policy_passed=policy_passed,
            )

            evolution_report = (
                self.evolution_engine.evolve(
                    request,
                    bridge=bridge,
                    limits=limits,
                    execution=execution,
                )
            )

            results.append(
                CandidateOrchestrationResult(
                    evaluation=evaluation,
                    evolution=evolution_report,
                )
            )

        approved = any(
            result.evolution is not None
            and result.evolution.approved
            for result in results
        )

        return OrchestrationReport(
            identifier=identifier,
            status=OrchestrationStatus.COMPLETED,
            decision=decision,
            candidates=tuple(results),
            reason=(
                "At least one candidate passed the complete "
                "controlled evolution pipeline."
                if approved
                else (
                    "No candidate passed the complete "
                    "controlled evolution pipeline."
                )
            ),
        )

    def _ensure_experiment(
        self,
        candidate: OrchestrationCandidate,
    ):
        """
        Register the candidate's experiment if necessary.

        Existing experiments are reused without mutation.
        """

        try:
            return self.experiment_engine.get(
                candidate.experiment_id
            )
        except KeyError:
            experiment = self._create_experiment(
                candidate
            )

            self.experiment_engine.register(
                experiment
            )

            return experiment

    @staticmethod
    def _create_experiment(
        candidate: OrchestrationCandidate,
    ):
        from .experiment import Experiment

        return Experiment(
            identifier=candidate.experiment_id,
            hypothesis=candidate.hypothesis,
            candidate=candidate.experiment_candidate,
            criteria=candidate.criteria,
      )
