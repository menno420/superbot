"""Governance in-process cache: version-stamped, tier-keyed.

Layer: models → events → cache.
Imports only from governance.models (and stdlib/typing).

When a guild has role-scoped overrides the role_ids frozenset is added to
the key so that members with different roles are not served identical cached
results.  See _guild_has_role_overrides below.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Protocol

# ---------------------------------------------------------------------------
# GovernanceCacheBackend Protocol (used by Step 10)
# ---------------------------------------------------------------------------


class GovernanceCacheBackend(Protocol):
    async def get(self, key: str) -> Any | None: ...

    async def set(self, key: str, value: Any, ttl: int) -> None: ...

    async def invalidate_pattern(self, pattern: str) -> None: ...


# ---------------------------------------------------------------------------
# Module-level in-process cache state
# ---------------------------------------------------------------------------

_CACHE: dict[tuple, tuple[float, Any]] = {}
_CACHE_VERSION: dict[int, int] = {}  # guild_id → version counter
_CACHE_LOCK = asyncio.Lock()
_CACHE_TTL = 60.0
# Raised from 2000 to 50000 to avoid O(n) scan on large multi-guild deployments.
_CACHE_CLEANUP_THRESHOLD = 50_000

# Tracks guilds that have at least one role-scoped visibility override in DB.
# Cleared by forget_guild() when bot leaves the guild.
_guild_has_role_overrides: dict[int, bool] = {}

# Subsystems whose cog failed to load at startup.
# Populated by register_failed_subsystems() from bot1._load_cogs().
# Treated as SubsystemState.INTERNAL so they are invisible to users.
_FAILED_SUBSYSTEMS: set[str] = set()


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _cache_ver(guild_id: int) -> int:
    return _CACHE_VERSION.get(guild_id, 0)


def _cache_key(
    guild_id: int,
    channel_id: int | None,
    tier: str,
    role_ids: frozenset[int] = frozenset(),
    *,
    thread_id: int | None = None,
) -> tuple:
    # RC-2 (ISSUE-016): thread_id is part of the cache identity.  For a thread
    # context the resolver passes the *parent* channel id as channel_id
    # (GovernanceContext.from_* set channel_id = thread.parent_id), so two
    # sibling threads — and the threadless parent channel itself — would
    # otherwise collide on a single channel-keyed entry and a thread-scoped
    # override would bleed across them.  Keying on thread_id keeps each thread
    # (and the parent, thread_id=None) isolated.
    if _guild_has_role_overrides.get(guild_id, False) and role_ids:
        # Phase 3.1: Include only the stable hash of role IDs rather than the raw
        # frozenset.  Two users with different role sets but identical governance-
        # relevant visibility will still get separate entries (hash collisions are
        # benign — a miss just triggers a fresh resolution).  This keeps keys small
        # and prevents combinatorial cache explosion in large guilds.
        role_fingerprint = hash(role_ids)
        return (
            guild_id,
            _cache_ver(guild_id),
            channel_id,
            thread_id,
            tier,
            role_fingerprint,
        )
    return (guild_id, _cache_ver(guild_id), channel_id, thread_id, tier)


def _cache_get(key: tuple) -> Any:
    entry = _CACHE.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.monotonic() - ts > _CACHE_TTL:
        return None
    return value


def _cache_set(key: tuple, value: Any) -> None:
    _CACHE[key] = (time.monotonic(), value)
    # Lazy cleanup: remove TTL-expired entries.  Threshold raised to 50k to avoid
    # frequent O(n) scans on large multi-guild deployments (Phase 3.1).
    if len(_CACHE) > _CACHE_CLEANUP_THRESHOLD:
        cutoff = time.monotonic() - _CACHE_TTL
        stale = [k for k, (ts, _) in _CACHE.items() if ts < cutoff]
        for k in stale:
            _CACHE.pop(k, None)


# ---------------------------------------------------------------------------
# Public cache management functions
# ---------------------------------------------------------------------------


def invalidate_guild_cache(guild_id: int) -> None:
    """Increment version counter — old keys become unreachable (O(1))."""
    _CACHE_VERSION[guild_id] = _cache_ver(guild_id) + 1


def forget_guild(guild_id: int) -> None:
    """Remove visibility cache state for a guild.

    Called from guild_lifecycle.teardown() when the bot leaves a guild.
    Note: capability execution override state lives in governance.execution and
    must be cleared via execution.forget_guild_capabilities() separately —
    see guild_lifecycle.py for the complete teardown sequence.
    """
    _CACHE_VERSION.pop(guild_id, None)
    _guild_has_role_overrides.pop(guild_id, None)


def register_failed_subsystems(subsystems: set[str]) -> None:
    """Mark subsystems whose cog failed to load as INTERNAL (invisible to users).

    Call this from _load_cogs() after all extension loads complete.
    Failed subsystems remain in the registry (no mutation) but are treated as
    SubsystemState.INTERNAL so they never appear in help menus or governance
    responses — preventing "command not found" confusion after partial boot.
    """
    _FAILED_SUBSYSTEMS.update(subsystems)


# ---------------------------------------------------------------------------
# Diagnostics registration — Phase S1.3
# ---------------------------------------------------------------------------

from services import diagnostics_service as _diag  # noqa: E402


def _diagnostics_snapshot() -> dict[str, object]:
    """Snapshot of governance cache state for ``!platform caches``."""
    return {
        "size": len(_CACHE),
        "guilds_versioned": len(_CACHE_VERSION),
        "guilds_with_role_overrides": sum(_guild_has_role_overrides.values()),
        "failed_subsystems": sorted(_FAILED_SUBSYSTEMS),
    }


_diag.register("governance_cache", _diagnostics_snapshot)
