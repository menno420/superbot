"""Phase 1a — Capability decoration for subsystem methods.

The :func:`capability` decorator marks a function or method as
implementing a capability declared in
:data:`utils.subsystem_registry.SUBSYSTEMS`.  At decoration time the
qualname is added to a reverse map keyed by capability string; the
``!platform capability-map`` admin command (Phase 4.5) surfaces this
map for governance audits.

The decorator is intentionally a thin metadata pass-through — it does
not implement authorization, governance, or any runtime behavior.
Authorization lives in :mod:`core.runtime.ui_permissions` for UI
surfaces and in :class:`~governance.writes.GovernanceMutationPipeline`
for state mutations; this decorator only records the relationship
between code and declared capability.

Validation that every decorated capability exists in
:data:`SUBSYSTEMS` runs at registry validation time
(:func:`utils.subsystem_registry.validate_registry`).  Decoration time
remains side-effect-free aside from the usage-map entry.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger("bot.subsystem_capabilities")

F = TypeVar("F", bound=Callable[..., Any])

# Reverse map: capability_string -> sorted list of "module.qualname" descriptors.
_USAGES: dict[str, list[str]] = {}


def capability(name: str) -> Callable[[F], F]:
    """Decorator marking a callable as implementing capability ``name``.

    ``name`` must be a three-part ``{subsystem}.{resource}.{action}``
    string.  The decorator records the decorated callable's
    ``module.qualname`` in the reverse map; runtime semantics are
    unchanged.

    Use sites typically look like::

        class EconomyCog(commands.Cog):
            @capability("economy.shop.buy")
            async def buy_item(self, ctx, item_id: int) -> None:
                ...

    The wrapper preserves the wrapped callable's signature via
    :func:`functools.wraps`; it does not alter the call semantics.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        qualname = f"{func.__module__}.{func.__qualname__}"
        usages = _USAGES.setdefault(name, [])
        if qualname not in usages:
            usages.append(qualname)
            usages.sort()
        # Introspection marker — Phase 4.5 governance diagnostics reads this.
        wrapper.__capability__ = name  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator


def get_capability_usages() -> dict[str, list[str]]:
    """Return a copy of the capability → usage-list reverse map."""
    return {cap: list(uses) for cap, uses in _USAGES.items()}


def get_usages_for(name: str) -> list[str]:
    """Return the sorted list of qualnames decorated with capability ``name``."""
    return list(_USAGES.get(name, ()))


def declared_capabilities() -> list[str]:
    """Return all decorated capability strings, sorted."""
    return sorted(_USAGES)


def _reset_for_tests() -> None:
    """Wipe the usage map.  Tests call this in their setup/teardown fixture."""
    _USAGES.clear()


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _capability_map_snapshot() -> dict[str, Any]:
    """Snapshot provider for ``!platform capability-map``."""
    usages = get_capability_usages()
    return {
        "decorated_total": len(usages),
        "decorations_total": sum(len(v) for v in usages.values()),
        "by_capability": dict(sorted(usages.items())),
    }


def _register_diagnostics_providers() -> None:
    from services import diagnostics_service

    diagnostics_service.register("capability_map", _capability_map_snapshot)


_register_diagnostics_providers()


__all__ = [
    "capability",
    "declared_capabilities",
    "get_capability_usages",
    "get_usages_for",
]
