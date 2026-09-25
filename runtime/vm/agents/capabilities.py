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

def require_capability(
    context: AgentContext,
    capability: str,
) -> None:
    """Require a capability or raise a runtime error."""

context.require_capability(capability)
