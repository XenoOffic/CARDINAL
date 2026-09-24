from __future__ import annotations

from dataclasses import dataclass

from .core import EvolutionHypothesis


@dataclass(frozen=True)
class HypothesisMetrics:
    """Quality metrics for a hypothesis set."""

    total: int
    average_confidence: float
    average_risk: float
    average_evidence_strength: float


class HypothesisMetricsEngine:
    """Calculates deterministic hypothesis metrics."""

    def calculate(
        self,
        hypotheses: tuple[
            EvolutionHypothesis, ...
        ],
    ) -> HypothesisMetrics:
        if not hypotheses:
            return HypothesisMetrics(
                total=0,
                average_confidence=0.0,
                average_risk=0.0,
                average_evidence_strength=0.0,
            )

        return HypothesisMetrics(
            total=len(hypotheses),
            average_confidence=(
                sum(
                    item.confidence
                    for item in hypotheses
                )
                / len(hypotheses)
            ),
            average_risk=(
                sum(
                    item.risk
                    for item in hypotheses
                )
                / len(hypotheses)
            ),
            average_evidence_strength=(
                sum(
                    item.evidence.average_strength
                    for item in hypotheses
                )
                / len(hypotheses)
            ),
        )
