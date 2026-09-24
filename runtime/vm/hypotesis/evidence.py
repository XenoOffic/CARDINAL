from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import EvidenceType


@dataclass(frozen=True)
class Evidence:
    """A single observable fact used by hypothesis reasoning."""

    identifier: str
    evidence_type: EvidenceType
    source: str
    value: Any
    description: str
    strength: float = 1.0

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError(
                "identifier cannot be empty."
            )

        if not self.source:
            raise ValueError(
                "source cannot be empty."
            )

        if not self.description:
            raise ValueError(
                "description cannot be empty."
            )

        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(
                "strength must be between 0 and 1."
            )


@dataclass(frozen=True)
class EvidenceSet:
    """Immutable collection of evidence."""

    items: tuple[Evidence, ...] = field(
        default_factory=tuple
    )

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def average_strength(self) -> float:
        if not self.items:
            return 0.0

        return sum(
            item.strength
            for item in self.items
        ) / len(self.items)

    def by_type(
        self,
        evidence_type: EvidenceType,
    ) -> tuple[Evidence, ...]:
        return tuple(
            item
            for item in self.items
            if item.evidence_type == evidence_type
        )

    def add(
        self,
        evidence: Evidence,
    ) -> EvidenceSet:
        return EvidenceSet(
            items=self.items + (evidence,)
        )
