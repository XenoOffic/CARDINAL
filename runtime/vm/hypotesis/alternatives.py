from __future__ import annotations

from .core import EvolutionHypothesis
from .types import (
    HypothesisType,
    ReasoningMode,
)


class AlternativeGenerator:
    """Produces alternative explanations for a hypothesis."""

    def __init__(
        self,
        *,
        max_alternatives: int = 3,
    ) -> None:
        if max_alternatives <= 0:
            raise ValueError(
                "max_alternatives must be greater than zero."
            )

        self.max_alternatives = (
            max_alternatives
        )

    def generate(
        self,
        hypothesis: EvolutionHypothesis,
    ) -> tuple[EvolutionHypothesis, ...]:
        alternatives: list[
            EvolutionHypothesis
        ] = []

        if (
            hypothesis.hypothesis_type
            == HypothesisType.PERFORMANCE
        ):
            alternatives.extend(
                self._performance(hypothesis)
            )

        elif (
            hypothesis.hypothesis_type
            == HypothesisType.RELIABILITY
        ):
            alternatives.extend(
                self._reliability(hypothesis)
            )

        elif (
            hypothesis.hypothesis_type
            == HypothesisType.SCHEDULING
        ):
            alternatives.extend(
                self._scheduling(hypothesis)
            )

        return tuple(
            alternatives[
                : self.max_alternatives
            ]
        )

    @staticmethod
    def _performance(
        parent: EvolutionHypothesis,
    ) -> list[EvolutionHypothesis]:
        return [
            EvolutionHypothesis(
                identifier=(
                    f"{parent.identifier}:resource"
                ),
                statement=(
                    "Resource pressure may be "
                    "contributing to the performance issue."
                ),
                rationale=(
                    "Performance degradation can "
                    "originate from resource pressure."
                ),
                expected_outcome=(
                    "Reduced resource pressure "
                    "and improved performance."
                ),
                hypothesis_type=(
                    HypothesisType.RESOURCE
                ),
                reasoning_mode=(
                    ReasoningMode.ABDUCTIVE
                ),
                confidence=0.55,
                risk=0.25,
                evidence=parent.evidence,
                parent_identifier=(
                    parent.identifier
                ),
            ),
            EvolutionHypothesis(
                identifier=(
                    f"{parent.identifier}:architecture"
                ),
                statement=(
                    "An architectural bottleneck may "
                    "be contributing to the slowdown."
                ),
                rationale=(
                    "Repeated slow behavior can "
                    "originate from structural bottlenecks."
                ),
                expected_outcome=(
                    "Improved throughput without "
                    "uncontrolled architectural changes."
                ),
                hypothesis_type=(
                    HypothesisType.ARCHITECTURE
                ),
                reasoning_mode=(
                    ReasoningMode.ABDUCTIVE
                ),
                confidence=0.50,
                risk=0.45,
                evidence=parent.evidence,
                parent_identifier=(
                    parent.identifier
                ),
            ),
        ]

    @staticmethod
    def _reliability(
        parent: EvolutionHypothesis,
    ) -> list[EvolutionHypothesis]:
        return [
            EvolutionHypothesis(
                identifier=(
                    f"{parent.identifier}:state"
                ),
                statement=(
                    "Unexpected runtime state may "
                    "be contributing to the failures."
                ),
                rationale=(
                    "Failures can originate from "
                    "incorrect or unexpected state."
                ),
                expected_outcome=(
                    "Improved state consistency."
                ),
                hypothesis_type=(
                    HypothesisType.CORRECTNESS
                ),
                reasoning_mode=(
                    ReasoningMode.ABDUCTIVE
                ),
                confidence=0.55,
                risk=0.30,
                evidence=parent.evidence,
                parent_identifier=(
                    parent.identifier
                ),
            )
        ]

    @staticmethod
    def _scheduling(
        parent: EvolutionHypothesis,
    ) -> list[EvolutionHypothesis]:
        return [
            EvolutionHypothesis(
                identifier=(
                    f"{parent.identifier}:contention"
                ),
                statement=(
                    "Scheduler contention may be "
                    "contributing to the observed latency."
                ),
                rationale=(
                    "Competing runtime work can "
                    "increase scheduling latency."
                ),
                expected_outcome=(
                    "Reduced contention while "
                    "preserving fairness."
                ),
                hypothesis_type=(
                    HypothesisType.SCHEDULING
                ),
                reasoning_mode=(
                    ReasoningMode.COMPARATIVE
                ),
                confidence=0.55,
                risk=0.35,
                evidence=parent.evidence,
                parent_identifier=(
                    parent.identifier
                ),
            )
        ]
