from __future__ import annotations

from ..decision import (
    DecisionAction,
    RuntimeDecision,
)
from .core import EvolutionHypothesis
from .reasoning import HypothesisReasoner
from .types import (
    HypothesisType,
)


class HypothesisGenerator:
    """
    Generates bounded hypotheses from runtime decisions.

    Generation produces descriptions only.
    """

    def __init__(
        self,
        reasoner: HypothesisReasoner | None = None,
        *,
        max_hypotheses: int = 5,
    ) -> None:
        if max_hypotheses <= 0:
            raise ValueError(
                "max_hypotheses must be greater than zero."
            )

        self.reasoner = (
            reasoner
            if reasoner is not None
            else HypothesisReasoner()
        )
        self.max_hypotheses = max_hypotheses

    def generate(
        self,
        decision: RuntimeDecision,
    ) -> tuple[EvolutionHypothesis, ...]:
        if (
            decision.action
            == DecisionAction.IGNORE
        ):
            return ()

        reasoning = self.reasoner.reason(
            decision
        )

        target = decision.target

        if (
            decision.action
            == DecisionAction.MONITOR
        ):
            return self._performance(
                decision,
                reasoning,
                target,
            )[: self.max_hypotheses]

        if (
            decision.action
            == DecisionAction.INVESTIGATE
        ):
            return self._reliability(
                decision,
                reasoning,
                target,
            )[: self.max_hypotheses]

        if (
            decision.action
            == DecisionAction.VERIFY
        ):
            return self._verification(
                decision,
                reasoning,
                target,
            )[: self.max_hypotheses]

        return ()

    @staticmethod
    def _performance(
        decision: RuntimeDecision,
        reasoning,
        target: str,
    ) -> list[EvolutionHypothesis]:
        return [
            EvolutionHypothesis(
                identifier=(
                    f"hypothesis:performance:{target}"
                ),
                statement=(
                    f"Performance of {target} "
                    "may be improved."
                ),
                rationale=(
                    reasoning.conclusion
                ),
                expected_outcome=(
                    "Reduced execution duration "
                    "without regression."
                ),
                hypothesis_type=(
                    HypothesisType.PERFORMANCE
                ),
                reasoning_mode=(
                    reasoning.mode
                ),
                confidence=(
                    reasoning.confidence
                ),
                risk=0.30,
                evidence=reasoning.evidence,
                metadata={
                    "decision_target": target,
                },
            ),
            EvolutionHypothesis(
                identifier=(
                    f"hypothesis:scheduling:{target}"
                ),
                statement=(
                    f"Scheduling behavior around "
                    f"{target} may contribute to "
                    "observed latency."
                ),
                rationale=(
                    "Execution duration can be "
                    "affected by scheduling behavior."
                ),
                expected_outcome=(
                    "Lower latency while preserving "
                    "scheduler correctness."
                ),
                hypothesis_type=(
                    HypothesisType.SCHEDULING
                ),
                reasoning_mode=(
                    ReasoningMode.COMPARATIVE
                ),
                confidence=0.65,
                risk=0.35,
                evidence=reasoning.evidence,
                metadata={
                    "decision_target": target,
                },
            ),
        ]

    @staticmethod
    def _reliability(
        decision: RuntimeDecision,
        reasoning,
        target: str,
    ) -> list[EvolutionHypothesis]:
        return [
            EvolutionHypothesis(
                identifier=(
                    f"hypothesis:reliability:{target}"
                ),
                statement=(
                    f"Reliability of {target} "
                    "may be improved."
                ),
                rationale=(
                    reasoning.conclusion
                ),
                expected_outcome=(
                    "Lower runtime error rate "
                    "while preserving behavior."
                ),
                hypothesis_type=(
                    HypothesisType.RELIABILITY
                ),
                reasoning_mode=(
                    reasoning.mode
                ),
                confidence=(
                    reasoning.confidence
                ),
                risk=0.25,
                evidence=reasoning.evidence,
                metadata={
                    "decision_target": target,
                },
            ),
            EvolutionHypothesis(
                identifier=(
                    f"hypothesis:correctness:{target}"
                ),
                statement=(
                    f"Incorrect state transitions "
                    f"may contribute to failures "
                    f"in {target}."
                ),
                rationale=(
                    "Repeated failures can indicate "
                    "incorrect runtime behavior."
                ),
                expected_outcome=(
                    "Fewer failures without "
                    "introducing new regressions."
                ),
                hypothesis_type=(
                    HypothesisType.CORRECTNESS
                ),
                reasoning_mode=(
                    ReasoningMode.ABDUCTIVE
                ),
                confidence=0.70,
                risk=0.30,
                evidence=reasoning.evidence,
                metadata={
                    "decision_target": target,
                },
            ),
        ]

    @staticmethod
    def _verification(
        decision: RuntimeDecision,
        reasoning,
        target: str,
    ) -> list[EvolutionHypothesis]:
        return [
            EvolutionHypothesis(
                identifier=(
                    f"hypothesis:verification:{target}"
                ),
                statement=(
                    f"Additional verification of "
                    f"{target} may reveal the "
                    "underlying cause."
                ),
                rationale=(
                    reasoning.conclusion
                ),
                expected_outcome=(
                    "Increase confidence in the "
                    "identified runtime behavior."
                ),
                hypothesis_type=(
                    HypothesisType.CORRECTNESS
                ),
                reasoning_mode=(
                    ReasoningMode.DEDUCTIVE
                ),
                confidence=(
                    reasoning.confidence
                ),
                risk=0.20,
                evidence=reasoning.evidence,
                metadata={
                    "decision_target": target,
                },
            )
              ]
