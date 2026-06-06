"""Centralized diagnostics registry — Phase S1.3.

State class: **process-local runtime** — see ``docs/architecture.md``
§"State classification".

A name-keyed registry of snapshot providers.  Each platform primitive
registers a zero-arg callable that returns its current state snapshot
(serializable: dict / dataclass / NamedTuple) suitable for display in
the ``!platform <name>`` admin commands shipping in Phase S2.5.

The registry is intentionally read-only at admin command time —
providers never mutate state; they only observe.  This means
diagnostics commands can never corrupt runtime state by being run too
often, in the wrong order, or under load.

Primitives self-register at import time, mirroring the
``persistent_views`` registration pattern.  Re-registration is allowed
(hot-reload-friendly) and overwrites with a debug-level log line so
ops can spot accidental dupes.

Substitution boundary: stays process-local (purely diagnostic).

Public surface:
    register(name, provider)        → None
    snapshot(name)                  → Any (whatever the provider returned)
    snapshot_all()                  → dict[str, Any]
    registered_names()              → list[str]
    unregister(name)                → None
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("bot.diagnostics")

# Name → provider callable.  Providers are sync; if a primitive ever
# needs to surface DB state for diagnostics, it should expose it via
# Prometheus or an async helper invoked from the admin command — not
# block snapshot() on I/O.
_PROVIDERS: dict[str, Callable[[], Any]] = {}


def register(name: str, provider: Callable[[], Any]) -> None:
    """Register ``provider`` under ``name``.

    Re-registration is allowed (hot-reload-friendly) and emits a
    DEBUG-level log entry so accidental duplicates are visible.
    """
    if name in _PROVIDERS:
        logger.debug("diagnostics_service: re-registering provider %r", name)
    _PROVIDERS[name] = provider


def unregister(name: str) -> None:
    """Remove the provider registered under ``name``.  No-op if absent."""
    _PROVIDERS.pop(name, None)


def snapshot(name: str) -> Any:
    """Invoke the provider registered under ``name`` and return its result.

    Raises ``KeyError`` if no provider is registered — the admin command
    surfaces this as a clear error rather than silently returning None.
    """
    if name not in _PROVIDERS:
        raise KeyError(
            f"No diagnostics provider registered for {name!r}. "
            f"Known: {sorted(_PROVIDERS)}",
        )
    return _PROVIDERS[name]()


def snapshot_all() -> dict[str, Any]:
    """Invoke every registered provider; return a name → snapshot mapping.

    Provider failures are caught and surfaced as
    ``{"_error": "<message>"}`` so one broken provider does not blank
    the full diagnostic page.
    """
    result: dict[str, Any] = {}
    # Iterate a stable copy: a provider may lazily import a module that
    # self-registers another provider on first call (common during startup),
    # which would otherwise raise "dict changed size during iteration".
    for name, provider in list(_PROVIDERS.items()):
        try:
            result[name] = provider()
        except Exception as exc:
            logger.warning(
                "diagnostics_service: provider %r raised %s",
                name,
                exc,
                exc_info=True,
            )
            result[name] = {"_error": f"{type(exc).__name__}: {exc}"}
    return result


def registered_names() -> list[str]:
    """Return registered provider names, alphabetically sorted."""
    return sorted(_PROVIDERS)


# ---------------------------------------------------------------------------
# Test surface — module-state reset.  Not used in production.
# ---------------------------------------------------------------------------


def _reset_for_tests() -> None:
    """Wipe the registry.  Tests call this in their setup/teardown fixture."""
    _PROVIDERS.clear()
