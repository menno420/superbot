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
_NO_OVERRIDE = object()  # sentinel for negative cache entries

# Tracks guilds that have at least one role-scoped visibility override in DB.
# Set to True by set_subsystem_visibility() when scope_type='role'.
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
) -> tuple:
    if _guild_has_role_overrides.get(guild_id, False):
        return (guild_id, _cache_ver(guild_id), channel_id, tier, role_ids)
    return (guild_id, _cache_ver(guild_id), channel_id, tier)


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
    # Lazy cleanup: remove entries from previous versions (unreachable anyway)
    if len(_CACHE) > 2000:
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
    """Remove all module-level state for a guild.

    Call this from an on_guild_remove event handler so that per-guild dicts
    do not grow unbounded as the bot joins and leaves servers.
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
