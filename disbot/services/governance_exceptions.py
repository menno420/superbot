"""Backward-compatible re-export of the governance exception hierarchy.

The canonical home for these types is :mod:`utils.governance_exceptions`. They
were moved out of ``services/`` so the ``governance/`` layer can import them
without crossing the ``governance → services`` layer boundary (``governance``
may import ``utils`` but not ``services`` — see ``docs/architecture.md``).

This module re-exports every name so existing ``from services.governance_exceptions
import ...`` call sites keep resolving unchanged. New code should import from
``utils.governance_exceptions`` directly.
"""

from __future__ import annotations

from utils.governance_exceptions import (
    CapabilityNamespaceError,
    CircularDependencyError,
    GovernanceError,
    GovernanceUpgradeError,
    RegistryValidationError,
    UnauthorizedGovernanceWriteError,
)

__all__ = [
    "GovernanceError",
    "RegistryValidationError",
    "CircularDependencyError",
    "CapabilityNamespaceError",
    "GovernanceUpgradeError",
    "UnauthorizedGovernanceWriteError",
]
