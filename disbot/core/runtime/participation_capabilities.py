"""Phase 1b — Capability decoration for per-user mutations.

Sibling of :mod:`core.runtime.subsystem_capabilities` for the
participation runtime.  The :func:`user_capability` decorator marks a
function or method as performing a per-user state mutation, in a
**separate namespace** from guild-level governance capabilities.

Why a separate decorator + registry:

* Guild-level capabilities (``moderation.warn.apply``) require
  moderator-or-higher tier (Phase 4.5's
  :class:`access_control_service`).
* User-level capabilities (``user.xp.toggle_levelup``) are authorized
  via the :class:`ParticipationMutationPipeline` from Phase 2c, whose
  authority model is "self, or moderator-or-higher" — fundamentally
  different from governance writes.
* Mixing the two namespaces would let an audit miss "every place we
  mutate per-user state" because the same call site would match both
  decorators.

Like :func:`subsystem_capabilities.capability`, this decorator is
metadata-only — it does not enforce authorization at decoration time.
Phase 2c's :class:`ParticipationMutationPipeline` performs the actual
authority check at mutation time.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger("bot.participation_capabilities")

F = TypeVar("F", bound=Callable[..., Any])

# Reverse map: user-capability-string -> sorted "module.qualname" list.
_USAGES: dict[str, list[str]] = {}


def user_capability(name: str) -> Callable[[F], F]:
    """Decorator marking a callable as performing a per-user mutation.

    ``name`` should be a dotted user-capability string conventionally
    prefixed ``user.`` (e.g. ``"user.xp.toggle_levelup"``).  The prefix
    is not enforced at decoration time, but Phase 6's identity contract
    extension validates the convention.

    The decorator preserves call semantics; only metadata is recorded.
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
        wrapper.__user_capability__ = name  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator


def get_user_capability_usages() -> dict[str, list[str]]:
    """Return a copy of the user-capability → usage-list reverse map."""
    return {cap: list(uses) for cap, uses in _USAGES.items()}


def get_usages_for(name: str) -> list[str]:
    """Return the sorted list of qualnames decorated with user-capability ``name``."""
    return list(_USAGES.get(name, ()))


def declared_user_capabilities() -> list[str]:
    """Return all decorated user-capability strings, sorted."""
    return sorted(_USAGES)


def _reset_for_tests() -> None:
    """Wipe the usage map.  Tests call this in their setup/teardown fixture."""
    _USAGES.clear()


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _user_capability_map_snapshot() -> dict[str, Any]:
    """Snapshot provider for ``!platform user-capability-map``."""
    usages = get_user_capability_usages()
    return {
        "decorated_total": len(usages),
        "decorations_total": sum(len(v) for v in usages.values()),
        "by_capability": dict(sorted(usages.items())),
    }


def _register_diagnostics_providers() -> None:
    from services import diagnostics_service

    diagnostics_service.register(
        "user_capability_map",
        _user_capability_map_snapshot,
    )


_register_diagnostics_providers()


__all__ = [
    "declared_user_capabilities",
    "get_user_capability_usages",
    "get_usages_for",
    "user_capability",
]
