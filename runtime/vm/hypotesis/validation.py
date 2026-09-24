from __future__ import annotations

from dataclasses import dataclass

from .core import EvolutionHypothesis


@dataclass(frozen=True)
class ValidationResult:
    """Result of structural hypothesis validation."""

    valid: bool
    reasons: tuple[str, ...]

    @property
    def count(self) -> int:
        return len(self.reasons)


class HypothesisValidator:
    """Validates hypotheses before they enter ranking."""

    def validate(
        self,
        hypothesis: EvolutionHypothesis,
    ) -> ValidationResult:
        reasons: list[str] = []

        if hypothesis.evidence.count == 0:
            reasons.append(
                "Hypothesis has no supporting evidence."
            )

        if hypothesis.confidence < 0.25:
            reasons.append(
                "Hypothesis confidence is too low."
            )

        if hypothesis.risk > 0.90:
            reasons.append(
                "Hypothesis risk is too high."
            )

        if not hypothesis.statement.strip():
            reasons.append(
                "Hypothesis statement is empty."
            )

        return ValidationResult(
            valid=not reasons,
            reasons=tuple(reasons),
        )
