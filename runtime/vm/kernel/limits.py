from __future__ import annotations

from dataclasses import dataclass

from .errors import VMError


@dataclass
class ExecutionLimits:
    """Execution limits applied by the CARDINAL kernel."""

    instruction_budget: int | None = None
    instructions_executed: int = 0

    def __post_init__(self) -> None:
        self.set_budget(
            self.instruction_budget
        )

    def set_budget(
        self,
        budget: int | None,
    ) -> None:
        if budget is not None and budget <= 0:
            raise ValueError(
                "instruction_budget must be greater than zero."
            )

        self.instruction_budget = budget
        self.instructions_executed = 0

    def consume(self) -> None:
        self.instructions_executed += 1

        if (
            self.instruction_budget is None
        ):
            return

        if (
            self.instructions_executed
            > self.instruction_budget
        ):
            raise VMError(
                "Instruction limit exceeded."
            )

    def reset(self) -> None:
        self.instructions_executed = 0
