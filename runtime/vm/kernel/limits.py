from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExecutionLimits:
    """Execution limits applied by the CARDINAL kernel."""

    instruction_budget: int | None = None

    def __post_init__(self) -> None:
        if (
            self.instruction_budget is not None
            and self.instruction_budget <= 0
        ):
            raise ValueError(
                "instruction_budget must be greater than zero."
            )

    def reset(self) -> None:
        """Reset the active execution budget state."""
        return None
