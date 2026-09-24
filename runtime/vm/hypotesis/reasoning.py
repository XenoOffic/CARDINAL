from __future__ import annotations

from dataclasses import dataclass

from ..decision import RuntimeDecision
from .evidence import Evidence, EvidenceSet
from .types import (
    EvidenceType,
    ReasoningMode,
)


@dataclass(frozen=True)
class ReasoningResult:
    """Structured result of the reasoning stage."""

    mode: ReasoningMode
    conclusion: str
    evidence: EvidenceSet
    confidence: float


class HypothesisReasoner:
    """
    Deterministic reasoning layer.

    It does not execute actions or generate source code.
    """

    def reason(
        self,
        decision: RuntimeDecision,
    ) -> ReasoningResult:
        evidence_items: list[Evidence] = []

        for index, item in enumerate(
            decision.evidence
        ):
            evidence_items.append(
                Evidence(
                    identifier=(
                        f"evidence:{index}"
                    ),
                    evidence_type=(
                        EvidenceType.RUNTIME
                    ),
                    source=item.source,
                    value=item.value,
                    description=item.description,
                    strength=decision.confidence,
                )
            )

        evidence = EvidenceSet(
            items=tuple(evidence_items)
        )

        if decision.priority.value == "high":
            mode = ReasoningMode.ABDUCTIVE
        elif decision.priority.value == "medium":
            mode = ReasoningMode.COMPARATIVE
        else:
            mode = ReasoningMode.DEDUCTIVE

        return ReasoningResult(
            mode=mode,
            conclusion=decision.reason,
            evidence=evidence,
            confidence=decision.confidence,
            )
