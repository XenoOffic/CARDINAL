from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DiagnosticSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class SourceLocation:
    line: int
    column: int


@dataclass(frozen=True)
class Diagnostic:
    severity: DiagnosticSeverity
    message: str
    location: SourceLocation

    def __str__(self) -> str:
        return (
            f"{self.location.line}:{self.location.column}: "
            f"{self.severity.value}: {self.message}"
        )
