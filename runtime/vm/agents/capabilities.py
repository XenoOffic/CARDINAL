from __future__ import annotations

from .context import AgentContext


def grant_capability(
    context: AgentContext,
    capability: str,
) -> None:
    """Grant a capability to an agent context."""
    context.grant(capability)


def revoke_capability(
    context: AgentContext,
    capability: str,
) -> None:
    """Revoke a capability from an agent context."""
    context.revoke(capability)


def has_capability(
    context: AgentContext,
    capability: str,
) -> bool:
    """Return whether the context owns a capability."""
    return context.has_capability(capability)


def require_capability(
    context: AgentContext,
    capability: str,
) -> None:
    """Require a capability or raise VMError."""
    context.require_capability(capability)


__all__ = [
    "grant_capability",
    "revoke_capability",
    "has_capability",
    "require_capability",
]
