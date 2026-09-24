from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .evidence import EvidenceSet
from .types import (
    HypothesisStatus,
    HypothesisType,
    ReasoningMode,
)


@dataclass(frozen=True)
class EvolutionHypothesis:
    """
    Structured hypothesis about a possible improvement.

    A hypothesis is descriptive and non-executable.
    """

    identifier: str
    statement: str
    rationale: str
    expected_outcome: str
    hypothesis_type: HypothesisType
    reasoning_mode: ReasoningMode
    confidence: float
    risk: float
    evidence: EvidenceSet = field(
        default_factory=EvidenceSet
    )
    status: HypothesisStatus = (
        HypothesisStatus.GENERATED
    )
    parent_identifier: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError(
                "identifier cannot be empty."
            )

        if not self.statement:
            raise ValueError(
                "statement cannot be empty."
            )

        if not self.rationale:
            raise ValueError(
                "rationale cannot be empty."
            )

        if not self.expected_outcome:
            raise ValueError(
                "expected_outcome cannot be empty."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not 0.0 <= self.risk <= 1.0:
            raise ValueError(
                "risk must be between 0 and 1."
            )


@dataclass(frozen=True)
class HypothesisSet:
    """A bounded collection of competing hypotheses."""

    hypotheses: tuple[
        EvolutionHypothesis, ...
    ] = field(default_factory=tuple)

    @property
    def count(self) -> int:
        return len(self.hypotheses)

    def by_type(
        self,
        hypothesis_type: HypothesisType,
    ) -> tuple[EvolutionHypothesis, ...]:
        return tuple(
            hypothesis
            for hypothesis in self.hypotheses
            if hypothesis.hypothesis_type
            == hypothesis_type
        )
