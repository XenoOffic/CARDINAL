from __future__ import annotations

from dataclasses import dataclass

from .core import EvolutionHypothesis
from .validation import HypothesisValidator


@dataclass(frozen=True)
class RankedHypothesis:
    """Hypothesis with its deterministic ranking score."""

    hypothesis: EvolutionHypothesis
    score: float


class HypothesisRanker:
    """
    Ranks hypotheses using confidence, evidence
    strength and risk.
    """

    def __init__(
        self,
        validator: HypothesisValidator | None = None,
    ) -> None:
        self.validator = (
            validator
            if validator is not None
            else HypothesisValidator()
        )

    def rank(
        self,
        hypotheses: tuple[
            EvolutionHypothesis, ...
        ],
    ) -> tuple[RankedHypothesis, ...]:
        ranked: list[RankedHypothesis] = []

        for hypothesis in hypotheses:
            validation = self.validator.validate(
                hypothesis
            )

            if not validation.valid:
                continue

            score = (
                hypothesis.confidence
                * hypothesis.evidence.average_strength
                * (1.0 - hypothesis.risk)
            )

            ranked.append(
                RankedHypothesis(
                    hypothesis=hypothesis,
                    score=score,
                )
            )

        ranked.sort(
            key=lambda item: (
                -item.score,
                item.hypothesis.identifier,
            )
        )

        return tuple(ranked)
