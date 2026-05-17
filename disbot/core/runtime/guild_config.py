"""Generalized guild-runtime configuration cache (F-1).

State class: **cached config (derived)** — see ``docs/architecture.md``
§"State classification".

Caches mostly-static guild-level configuration with a TTL safety net
and explicit invalidation discipline.  Mirrors the proven shape of
``governance.cache`` (version-stamped reads, bounded size, lazy cleanup)
but is general-purpose: callers supply a ``loader`` callable that knows
how to fetch from authoritative state on miss.

Callers MUST go through a typed accessor in
``utils.guild_config_accessors`` rather than calling ``get`` with a
bare string key.  This is enforced by the AST invariant at
``tests/unit/invariants/test_guild_config_typed_accessors.py`` so that
a typo in a key string is a build failure, not a silent cross-consumer
bug.

Substitution boundary: Redis with TTL (Phase Sc work; see ADR-001).
The ``GuildConfigBackend`` Protocol below documents the interface.

Public surface:
    get(guild_id, key, *, loader)             → Awaitable[T]
    get_many(guild_id, keys, *, loader)       → Awaitable[dict[str, T]]
    invalidate(guild_id[, key])               → None
    forget_guild(guild_id)                    → None
    stats()                                   → CacheStats
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from services import metrics as _metrics

logger = logging.getLogger("bot.runtime.guild_config")

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Protocol — eventual substitution boundary (Redis backend, Phase Sc)
# ---------------------------------------------------------------------------


class GuildConfigBackend(Protocol):
    """Substitution interface for the in-process cache (future Redis backend).

    Documented now so the Phase Sc substitution work is mechanical, not a
    rewrite.  No production code consumes this Protocol today — the
    module-level functions below are the consumer surface.
    """

    async def get(self, guild_id: int, key: str) -> Any: ...

    async def set(
        self,
        guild_id: int,
        key: str,
        value: Any,
        ttl: float,
    ) -> None: ...

    async def invalidate(self, guild_id: int, key: str | None = None) -> None: ...


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

# Composite key: (guild_id, version, key).  Version stamp makes
# guild-wide invalidation O(1) — bumping the version makes every old
# entry's composite key unreachable on the next read.
_CACHE: dict[tuple[int, int, str], tuple[float, Any]] = {}
_VERSION: dict[int, int] = {}

DEFAULT_TTL_SECONDS: float = 60.0
# Conservative starting bound; raise if !platform caches shows pressure.
CACHE_CLEANUP_THRESHOLD: int = 10_000


@dataclass(frozen=True)
class CacheStats:
    """Snapshot of cache state for diagnostics / observability."""

    size: int
    versions_tracked: int


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _version(guild_id: int) -> int:
    """Return the current version stamp for ``guild_id`` (without inserting)."""
    return _VERSION.get(guild_id, 0)


def _make_key(guild_id: int, key: str) -> tuple[int, int, str]:
    """Build the composite cache key, lazily initialising the version stamp.

    Using ``setdefault`` here means ``_VERSION`` tracks every guild that
    has ever had a cached entry, not just those that have been
    invalidated.  This makes ``forget_guild``'s ``_VERSION.pop(...)``
    meaningful in all cases and gives ``stats().versions_tracked`` a
    diagnostic meaning ("guilds with cached state") instead of an
    operational accident ("guilds that have been invalidated").
    """
    return (guild_id, _VERSION.setdefault(guild_id, 0), key)


def _cache_lookup(composite: tuple[int, int, str]) -> tuple[bool, Any]:
    """Return ``(hit, value)``.  TTL-expired entries are treated as misses."""
    entry = _CACHE.get(composite)
    if entry is None:
        return False, None
    ts, value = entry
    if time.monotonic() - ts > DEFAULT_TTL_SECONDS:
        return False, None
    return True, value


def _cache_store(composite: tuple[int, int, str], value: Any) -> None:
    _CACHE[composite] = (time.monotonic(), value)
    if len(_CACHE) > CACHE_CLEANUP_THRESHOLD:
        _evict_stale()


def _evict_stale() -> None:
    """Drop TTL-expired entries.  Called when the cache crosses the bound."""
    cutoff = time.monotonic() - DEFAULT_TTL_SECONDS
    stale = [k for k, (ts, _) in _CACHE.items() if ts < cutoff]
    for k in stale:
        _CACHE.pop(k, None)


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


async def get(
    guild_id: int,
    key: str,
    *,
    loader: Callable[[], Awaitable[T]],
) -> T:
    """Return cached value for ``(guild_id, key)``; invoke ``loader`` on miss.

    Concurrent callers for the same key may each invoke ``loader`` (the
    last write wins).  Since ``loader`` is expected to be deterministic
    over short windows, this is wasted work, not a correctness issue.
    """
    composite = _make_key(guild_id, key)
    hit, value = _cache_lookup(composite)
    if hit:
        _metrics.guild_config_cache_hits.labels(key=key).inc()
        return value  # type: ignore[no-any-return]
    _metrics.guild_config_cache_misses.labels(key=key).inc()
    fresh = await loader()
    _cache_store(composite, fresh)
    _metrics.guild_config_cache_size.set(len(_CACHE))
    return fresh


async def get_many(
    guild_id: int,
    keys: list[str],
    *,
    loader: Callable[[list[str]], Awaitable[dict[str, T]]],
) -> dict[str, T]:
    """Batch variant: ``loader`` receives the missed keys, returns their values."""
    result: dict[str, Any] = {}
    missed: list[str] = []
    for k in keys:
        composite = _make_key(guild_id, k)
        hit, value = _cache_lookup(composite)
        if hit:
            _metrics.guild_config_cache_hits.labels(key=k).inc()
            result[k] = value
        else:
            _metrics.guild_config_cache_misses.labels(key=k).inc()
            missed.append(k)
    if missed:
        fetched = await loader(missed)
        for k, v in fetched.items():
            _cache_store(_make_key(guild_id, k), v)
            result[k] = v
        _metrics.guild_config_cache_size.set(len(_CACHE))
    return result


def invalidate(guild_id: int, key: str | None = None) -> None:
    """Invalidate cache entries.

    ``key=None`` bumps the guild version so every key for that guild
    becomes unreachable on the next read (O(1) wholesale invalidation;
    the orphan entries are reclaimed by the lazy cleanup sweep).  A
    specific ``key`` deletes only that entry's current-version key.

    MUST be called from the admin write paths that mutate the
    corresponding authoritative state.  TTL is a safety net, not the
    primary invalidation mechanism.
    """
    if key is None:
        _VERSION[guild_id] = _version(guild_id) + 1
        _metrics.guild_config_cache_invalidations.labels(scope="guild").inc()
        return
    composite = _make_key(guild_id, key)
    if composite in _CACHE:
        del _CACHE[composite]
    _metrics.guild_config_cache_invalidations.labels(scope="key").inc()


def forget_guild(guild_id: int) -> None:
    """Drop all cache state for ``guild_id``.

    Called from ``guild_lifecycle.teardown`` when the bot leaves a guild,
    so departed-guild state cannot accumulate process-locally.
    """
    _VERSION.pop(guild_id, None)
    # Proactively reclaim memory rather than relying on the version bump
    # plus the lazy cleanup sweep.  guild_remove is rare; O(N) is fine.
    stale = [k for k in _CACHE if k[0] == guild_id]
    for k in stale:
        _CACHE.pop(k, None)
    _metrics.guild_config_cache_size.set(len(_CACHE))


def stats() -> CacheStats:
    """Point-in-time cache snapshot, for ``!platform caches``."""
    return CacheStats(size=len(_CACHE), versions_tracked=len(_VERSION))


# ---------------------------------------------------------------------------
# Test surface — module-state reset.  Not used in production.
# ---------------------------------------------------------------------------


def _reset_for_tests() -> None:
    """Wipe module state.  Tests call this in their setup/teardown fixture."""
    _CACHE.clear()
    _VERSION.clear()


# ---------------------------------------------------------------------------
# Diagnostics registration — Phase S1.3
# ---------------------------------------------------------------------------

# Self-register a sync snapshot provider with the diagnostics registry so
# `!platform caches` (S2.5) can read the current cache size and tracked
# guild count without depending on the primitive's internal types.
from services import diagnostics_service as _diag  # noqa: E402


def _diagnostics_snapshot() -> dict[str, int]:
    s = stats()
    return {"size": s.size, "versions_tracked": s.versions_tracked}


_diag.register("guild_config", _diagnostics_snapshot)
