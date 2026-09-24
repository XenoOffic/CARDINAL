from __future__ import annotations

from enum import Enum


class HypothesisType(str, Enum):
    """Classification of a CARDINAL hypothesis."""

    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    RESOURCE = "resource"
    CORRECTNESS = "correctness"
    SCHEDULING = "scheduling"
    ARCHITECTURE = "architecture"
    BEHAVIORAL = "behavioral"
    SECURITY = "security"
    UNKNOWN = "unknown"


class ReasoningMode(str, Enum):
    """Reasoning strategy used to construct a hypothesis."""

    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    COMPARATIVE = "comparative"
    COUNTERFACTUAL = "counterfactual"


class HypothesisStatus(str, Enum):
    """Lifecycle state of a hypothesis."""

    GENERATED = "generated"
    VALIDATED = "validated"
    REJECTED = "rejected"
    TESTING = "testing"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    SUPERSEDED = "superseded"


class EvidenceType(str, Enum):
    """Origin of evidence supporting a hypothesis."""

    RUNTIME = "runtime"
    PERFORMANCE = "performance"
    ERROR = "error"
    RESOURCE = "resource"
    HISTORICAL = "historical"
    STRUCTURAL = "structural"
    EXPERIMENTAL = "experimental"
