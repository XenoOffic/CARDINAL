from __future__ import annotations

from dataclasses import dataclass, field

from ..decision import RuntimeDecision
from .alternatives import AlternativeGenerator
from .core import EvolutionHypothesis
from .generation import HypothesisGenerator
from .history import HypothesisHistory
from .metrics import (
    HypothesisMetrics,
    HypothesisMetricsEngine,
)
from .ranking import (
    HypothesisRanker,
    RankedHypothesis
)


@dataclass(frozen=True)
class HypothesisEngineReport:
    """Complete output of the hypothesis subsystem."""

    hypotheses: tuple[
        EvolutionHypothesis, ...
    ] = field(default_factory=tuple)

    ranked: tuple[
        RankedHypothesis, ...
    ] = field(default_factory=tuple)

    metrics: HypothesisMetrics = field(
        default_factory=lambda:
        HypothesisMetrics(
            total=0,
            average_confidence=0.0,
            average_risk=0.0,
            average_evidence_strength=0.0,
        )
    )

    @property
    def count(self) -> int:
        return len(self.hypotheses)

    @property
    def top(
        self,
    ) -> RankedHypothesis | None:
        if not self.ranked:
            return None

        return self.ranked[0]


class HypothesisEngine:
    """
    Central coordinator of CARDINAL's hypothesis subsystem.

    Pipeline:

        Decision
          ↓
        Reasoning
          ↓
        Generation
          ↓
        Alternatives
          ↓
        Validation
          ↓
        Ranking
          ↓
        Metrics
          ↓
        History
    """

    def __init__(
        self,
        *,
        max_hypotheses: int = 12,
        max_alternatives: int = 3,
        history: HypothesisHistory | None = None,
    ) -> None:
        if max_hypotheses <= 0:
            raise ValueError(
                "max_hypotheses must be greater than zero."
            )

        self.max_hypotheses = max_hypotheses

        self.generator = HypothesisGenerator(
            max_hypotheses=max_hypotheses
        )

        self.alternatives = AlternativeGenerator(
            max_alternatives=max_alternatives
        )

        self.ranker = HypothesisRanker()
        self.metrics_engine = (
            HypothesisMetricsEngine()
        )

        self.history = (
            history
            if history is not None
            else HypothesisHistory()
        )

    def analyze(
        self,
        decision: RuntimeDecision,
    ) -> HypothesisEngineReport:
        primary = list(
            self.generator.generate(
                decision
            )
        )

        all_hypotheses = list(primary)

        for hypothesis in primary:
            if len(all_hypotheses) >= (
                self.max_hypotheses
            ):
                break

            alternatives = (
                self.alternatives.generate(
                    hypothesis
                )
            )

            for alternative in alternatives:
                if len(all_hypotheses) >= (
                    self.max_hypotheses
                ):
                    break

                all_hypotheses.append(
                    alternative
                )

        hypotheses = tuple(
            all_hypotheses[
                : self.max_hypotheses
            ]
        )

        for hypothesis in hypotheses:
            self.history = (
                self.history.record(
                    hypothesis
                )
            )

        ranked = self.ranker.rank(
            hypotheses
        )

        metrics = (
            self.metrics_engine.calculate(
                hypotheses
            )
        )

        return HypothesisEngineReport(
            hypotheses=hypotheses,
            ranked=ranked,
            metrics=metrics,
          )
