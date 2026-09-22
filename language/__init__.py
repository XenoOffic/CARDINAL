"""
CARDINAL language package.

Contains the grammar, lexer, parser, AST,
type system and semantic analysis components.
"""
from .diagnostics import (
    Diagnostic,
    DiagnosticSeverity,
    SourceLocation,
)

__all__ = [
    "Diagnostic",
    "DiagnosticSeverity",
    "SourceLocation",
]
