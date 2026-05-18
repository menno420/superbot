"""Per-user participation cache — Phase 2c (PR-8).

Process-local cache over the four participation tables shipped in
migration 027.  Mirrors the design of ``core.runtime.guild_config``:
TTL-bounded entries with explicit invalidation primitives so PR-9's
``ParticipationMutationPipeline`` can drop the stale entry after every
write.

State class (per ``docs/architecture.md`` §"State classification"):

  **cached config (derived)** — the DB row is the canonical state.
  Cache entries may be evicted at any time.

Cache key shape: ``(user_id, guild_id)``.  One entry caches the full
four-table bundle for that ``(user, guild)`` pair so subsystem
accessors (``get_participation``, ``is_subscribed``, etc.) hit the
cache once and dispatch internally.

Cache eviction:

* **TTL** — each entry expires after ``_CACHE_TTL_SECS`` (default 300s,
  same window as the feature-flag evaluator).
* **Max size** — at most ``_CACHE_MAX_ENTRIES`` entries (default 50_000).
  Hit the cap → drop the oldest entries by ``inserted_at`` ordering.
  This is a coarse LRU-ish approximation; a real LRU is unnecessary
  because the working set is dominated by recently active users.
* **Explicit invalidation** — :func:`forget_user`,
  :func:`invalidate_user_guild`, :func:`forget_guild`,
  :func:`forget_all`.  PR-9 calls ``invalidate_user_guild`` after every
  mutation.
* **Guild teardown** — :func:`forget_guild` is the hook called from
  ``guild_lifecycle.teardown``.

This module is read-only against the DB.  Writes live in PR-9's
mutation pipeline; the pipeline calls back into this module's
invalidation primitives.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("bot.user_config")

# 5-minute TTL matches the feature-flag evaluator default — close
# enough that a user's mutation is reflected within one cache cycle
# even without explicit invalidation, but long enough to absorb the
# read pressure from any single interaction.
_CACHE_TTL_SECS = 300.0

# Soft upper bound on cache size.  Each entry holds the JSON-decoded
# bundle for one (user, guild) pair.  50k entries × ~1 KB each is
# ~50 MB, comfortably within process memory for any practical
# deployment.
_CACHE_MAX_ENTRIES = 50_000


@dataclass(frozen=True)
class CachedUserConfig:
    """One cached (user, guild) bundle.

    The fields mirror what ``utils.db.user_participation.list_for_user``
    returns.  Stored as plain dicts so the cache is JSON-friendly
    (and so the diagnostics provider can render them).
    """

    user_id: int
    guild_id: int
    participation: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    subscriptions: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    preferences: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    visibility_overrides: tuple[dict[str, Any], ...] = field(default_factory=tuple)


# Cache value: (CachedUserConfig, expires_at_monotonic, inserted_at_monotonic).
_CACHE: dict[tuple[int, int], tuple[CachedUserConfig, float, float]] = {}

# Metric counters — diagnostics provider snapshots these.
_HITS = 0
_MISSES = 0
_EVICTIONS = 0


def _evict_for_capacity() -> None:
    """Drop the oldest entries when ``_CACHE`` exceeds the soft cap.

    Coarse, not strict LRU — drops the bottom decile by
    ``inserted_at`` whenever the cap trips.  Cheaper than maintaining
    an ordered structure and good enough for participation, which is
    a low-volume read pattern compared to hot-path message dispatch.
    """
    global _EVICTIONS
    if len(_CACHE) <= _CACHE_MAX_ENTRIES:
        return
    sorted_keys = sorted(
        _CACHE.keys(),
        key=lambda k: _CACHE[k][2],  # inserted_at
    )
    drop_count = max(1, len(_CACHE) // 10)
    for key in sorted_keys[:drop_count]:
        _CACHE.pop(key, None)
        _EVICTIONS += 1


async def get(user_id: int, guild_id: int) -> CachedUserConfig:
    """Return the cached bundle for ``(user, guild)``; load on miss.

    Returns an empty :class:`CachedUserConfig` (all tuples empty) when
    the user has no rows in any of the four tables — that's the
    "not yet configured anything" state.  Typed accessors in
    :mod:`utils.user_config_accessors` interpret an empty bundle as
    "every concern returns its declared default".
    """
    global _HITS, _MISSES
    key = (user_id, guild_id)
    entry = _CACHE.get(key)
    now = time.monotonic()
    if entry is not None:
        cached, expires_at, _ = entry
        if expires_at >= now:
            _HITS += 1
            return cached
        # Expired — fall through to reload.
        _CACHE.pop(key, None)

    # Cache miss — load from DB.
    _MISSES += 1
    from utils.db import user_participation as up_db

    try:
        bundle = await up_db.list_for_user(user_id, guild_id)
    except Exception as exc:  # noqa: BLE001 — read path must not raise
        logger.warning(
            "user_config: list_for_user raised for user=%d guild=%d (%r); "
            "returning empty bundle",
            user_id,
            guild_id,
            exc,
        )
        bundle = {
            "participation": [],
            "subscriptions": [],
            "preferences": [],
            "visibility_overrides": [],
        }

    cached = CachedUserConfig(
        user_id=user_id,
        guild_id=guild_id,
        participation=tuple(bundle["participation"]),
        subscriptions=tuple(bundle["subscriptions"]),
        preferences=tuple(bundle["preferences"]),
        visibility_overrides=tuple(bundle["visibility_overrides"]),
    )
    _CACHE[key] = (cached, now + _CACHE_TTL_SECS, now)
    _evict_for_capacity()
    return cached


# ---------------------------------------------------------------------------
# Invalidation primitives.  PR-9's ParticipationMutationPipeline calls
# ``invalidate_user_guild`` after every write so subsequent reads see
# the new state.
# ---------------------------------------------------------------------------


def invalidate_user_guild(user_id: int, guild_id: int) -> bool:
    """Drop the cache entry for ``(user, guild)`` if present.

    Returns ``True`` when an entry was dropped, ``False`` otherwise.
    """
    return _CACHE.pop((user_id, guild_id), None) is not None


def forget_user(user_id: int) -> int:
    """Drop every cache entry for ``user_id`` (across all guilds).

    Returns the number of entries removed.
    """
    keys = [k for k in _CACHE if k[0] == user_id]
    for k in keys:
        _CACHE.pop(k, None)
    return len(keys)


def forget_guild(guild_id: int) -> int:
    """Drop every cache entry whose guild matches ``guild_id``.

    Called from ``guild_lifecycle.teardown`` so a re-invited guild
    does not observe stale per-user decisions.
    """
    keys = [k for k in _CACHE if k[1] == guild_id]
    for k in keys:
        _CACHE.pop(k, None)
    return len(keys)


def forget_all() -> int:
    """Drop the entire cache.  Returns the number of entries removed."""
    n = len(_CACHE)
    _CACHE.clear()
    return n


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


def _snapshot() -> dict[str, Any]:
    """Snapshot for the diagnostics provider.

    Returns counts only — the bundle content is not surfaced via
    diagnostics for privacy.
    """
    return {
        "cache_size": len(_CACHE),
        "cache_capacity": _CACHE_MAX_ENTRIES,
        "ttl_secs": _CACHE_TTL_SECS,
        "hits": _HITS,
        "misses": _MISSES,
        "evictions": _EVICTIONS,
    }


def _reset_for_tests() -> None:
    """Test helper — clear cache + reset counters."""
    global _HITS, _MISSES, _EVICTIONS
    _CACHE.clear()
    _HITS = 0
    _MISSES = 0
    _EVICTIONS = 0


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("user_config", _snapshot)


_register_diagnostics()


__all__ = [
    "CachedUserConfig",
    "forget_all",
    "forget_guild",
    "forget_user",
    "get",
    "invalidate_user_guild",
]
