"""Typed exception hierarchy for the governance layer.

All governance failures raise subclasses of :class:`GovernanceError`.
No bare ``ValueError`` or ``RuntimeError`` should originate from governance code.

These types live in ``utils/`` (not ``services/``) on purpose: the
``governance/`` layer raises them, and ``governance`` may import ``utils`` but
**not** ``services`` (layer contract — see ``docs/architecture.md``). Keeping
the exception classes here lets governance, services, cogs, and views all share
one definition without anyone crossing a layer boundary to reach it.

Backward compatibility: ``services.governance_exceptions`` re-exports every name
defined here, so existing ``from services.governance_exceptions import ...``
call sites continue to resolve unchanged.
"""

from __future__ import annotations


class GovernanceError(Exception):
    """Base class for all governance-layer errors."""


class RegistryValidationError(GovernanceError):
    """Registry integrity check failed during startup validation."""


class CircularDependencyError(RegistryValidationError):
    """Circular dependency detected in the subsystem dependency graph."""

    def __init__(self, node: str, neighbour: str) -> None:
        super().__init__(f"Circular dependency detected: '{node}' → '{neighbour}'")
        self.node = node
        self.neighbour = neighbour


class CapabilityNamespaceError(RegistryValidationError):
    """Capability does not follow the required {subsystem}.{resource}.{action} format,
    or uses a reserved namespace prefix (_internal, system, governance).
    """


class GovernanceUpgradeError(GovernanceError):
    """Governance schema version upgrade failed."""


class UnauthorizedGovernanceWriteError(GovernanceError):
    """Caller lacks the authority tier required to mutate governance state.

    Governance writes are an infrastructure boundary: even if the cog layer
    has already validated the user's Discord permissions, the governance
    pipeline re-validates to prevent authority escalation from coding mistakes.
    """


__all__ = [
    "GovernanceError",
    "RegistryValidationError",
    "CircularDependencyError",
    "CapabilityNamespaceError",
    "GovernanceUpgradeError",
    "UnauthorizedGovernanceWriteError",
]
