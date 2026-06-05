"""Feature stale-state cleanup provider registry (RC-7).

``session_gc`` owns *scheduling*; feature services own *what* stale state to
reclaim and the economic semantics of doing so — e.g. the ADR-002 refund on an
abandoned ``game_state`` row.  Feature services register a provider here, and
``session_gc`` invokes them all via :func:`run_all` without importing any
feature service.

Providers are async zero-arg callables returning a :class:`CleanupResult`.
Registration mirrors ``diagnostics_service`` / ``persistent_views``: it is
idempotent and re-registration overwrites with a DEBUG log line.

Layer: pure ``core`` — imports stdlib only, never a service (that is the whole
point: it lets ``session_gc`` drop its ``economy_service`` /
``game_state_service`` module imports).
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import NamedTuple

logger = logging.getLogger("bot.runtime.cleanup")


class CleanupResult(NamedTuple):
    """Counts returned by a cleanup provider (and aggregated by :func:`run_all`).

    It is a ``NamedTuple`` so callers can either unpack it
    (``removed, refunded = result``) or use attribute access.
    """

    removed: int = 0
    refunded: int = 0


CleanupProvider = Callable[[], Awaitable[CleanupResult]]

_PROVIDERS: dict[str, CleanupProvider] = {}


def register(name: str, provider: CleanupProvider) -> None:
    """Register ``provider`` under ``name``.

    Re-registration is allowed (hot-reload-friendly) and emits a DEBUG entry so
    accidental duplicates are visible.
    """
    if name in _PROVIDERS:
        logger.debug("cleanup_registry: re-registering provider %r", name)
    _PROVIDERS[name] = provider


def unregister(name: str) -> None:
    """Remove the provider registered under ``name``.  No-op if absent."""
    _PROVIDERS.pop(name, None)


def registered_names() -> list[str]:
    """Return registered provider names, alphabetically sorted."""
    return sorted(_PROVIDERS)


async def run_all() -> CleanupResult:
    """Invoke every registered provider and aggregate their counts.

    Each provider is isolated: an exception is logged and treated as a
    zero-count result, so one broken provider never blocks the rest of the GC
    sweep (mirrors the robustness the inline ``_sweep_stale_game_state`` had).
    """
    removed = 0
    refunded = 0
    for name, provider in list(_PROVIDERS.items()):
        try:
            res = await provider()
        except Exception as exc:
            logger.error("cleanup provider %r failed: %s", name, exc, exc_info=True)
            continue
        removed += res.removed
        refunded += res.refunded
    return CleanupResult(removed=removed, refunded=refunded)


def _reset_for_tests() -> None:
    """Wipe the registry.  Tests call this in their setup/teardown fixture."""
    _PROVIDERS.clear()
