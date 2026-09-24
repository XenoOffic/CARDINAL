from __future__ import annotations

from dataclasses import dataclass, field

from .core import EvolutionHypothesis
from .types import HypothesisStatus


@dataclass(frozen=True)
class HypothesisHistory:
    """Bounded historical record of generated hypotheses."""

    items: tuple[
        EvolutionHypothesis, ...
    ] = field(default_factory=tuple)
    max_items: int = 1000

    def __post_init__(self) -> None:
        if self.max_items <= 0:
            raise ValueError(
                "max_items must be greater than zero."
            )

    def record(
        self,
        hypothesis: EvolutionHypothesis,
    ) -> HypothesisHistory:
        items = (
            self.items + (hypothesis,)
        )

        if len(items) > self.max_items:
            items = items[-self.max_items :]

        return HypothesisHistory(
            items=items,
            max_items=self.max_items,
        )

    def find(
        self,
        identifier: str,
    ) -> EvolutionHypothesis | None:
        for hypothesis in reversed(self.items):
            if hypothesis.identifier == identifier:
                return hypothesis

        return None

    def by_status(
        self,
        status: HypothesisStatus,
    ) -> tuple[EvolutionHypothesis, ...]:
        return tuple(
            hypothesis
            for hypothesis in self.items
            if hypothesis.status == status
        )

    @property
    def count(self) -> int:
        return len(self.items)
