"""Typed accessors for the ``core.runtime.guild_config`` cache.

Every consumer of ``guild_config`` MUST import its accessor from this
module rather than calling ``guild_config.get(...)`` with a bare string
key.  Enforced by the AST invariant at
``tests/unit/invariants/test_guild_config_typed_accessors.py``.

The discipline:

    Cogs / views / services
        ↓
    utils.guild_config_accessors            ← canonical key strings live here
        ↓
    core.runtime.guild_config               ← the primitive

Each accessor owns:

  * a single canonical key string,
  * the typed return shape (dataclass / NamedTuple),
  * the loader callable that fetches from authoritative state on miss,
  * and the invalidation entry point its admin write paths call into.

Phase 0 of the platform roadmap introduced ``TypedAccessor[T]`` so new
accessors are mechanical to add (one ``TypedAccessor`` instance per
typed shape) and the discipline above is impossible to violate without
deliberate effort.

Accessors land here as consumers migrate.  Phase S2.2 added the XP
accessors; later cogs add theirs here as they migrate off
``db.get_setting`` hot-path calls.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from core.runtime import guild_config
from utils import db
from utils.settings_keys import XP_COOLDOWN, XP_MAX, XP_MIN

T = TypeVar("T")


class TypedAccessor(Generic[T]):
    """Bundle of (cache key, typed shape, loader, invalidator).

    Construct one per typed-shape consumer at module scope.  ``get`` and
    ``invalidate`` are the only public methods; both are thin wrappers
    over ``core.runtime.guild_config`` that keep the canonical key string
    private to this module.

    The generic parameter ``T`` is the dataclass / NamedTuple / primitive
    type the loader returns.  ``guild_config`` stores any picklable
    object; ``TypedAccessor`` only commits to the type discipline at the
    accessor boundary.
    """

    __slots__ = ("_cache_key", "_loader_factory")

    def __init__(
        self,
        cache_key: str,
        loader_factory: Callable[[int], Callable[[], Awaitable[T]]],
    ) -> None:
        """Bind the accessor to a cache key and a loader factory.

        ``loader_factory(guild_id)`` returns the zero-arg coroutine the
        cache invokes on a miss.  Keeping the factory parameterised by
        guild_id (rather than baking the guild into the closure at
        ``get`` time) lets ``TypedAccessor`` stay stateless.
        """
        self._cache_key = cache_key
        self._loader_factory = loader_factory

    async def get(self, guild_id: int) -> T:
        """Return the cached value for ``guild_id``; load on miss."""
        return await guild_config.get(
            guild_id,
            self._cache_key,
            loader=self._loader_factory(guild_id),
        )

    def invalidate(self, guild_id: int) -> None:
        """Drop the cached value for ``guild_id``."""
        guild_config.invalidate(guild_id, self._cache_key)


# ---------------------------------------------------------------------------
# XP listener config — consumed by cogs/xp_cog.py:on_message (S2.2)
# ---------------------------------------------------------------------------

# Defaults mirror the module-level constants in cogs/xp_cog.py.  They live
# here so the accessor is self-contained — the loader can compute the
# config without a circular import back into the cog.
_XP_DEFAULT_MIN: int = 15
_XP_DEFAULT_MAX: int = 25
_XP_DEFAULT_COOLDOWN: int = 60


@dataclass(frozen=True)
class XpConfig:
    """Cached XP-listener configuration for a single guild."""

    xp_min: int
    xp_max: int
    cooldown: int
    announce_channel: str  # "" when unset; cog interprets as "use source channel"


def _xp_config_loader(guild_id: int) -> Callable[[], Awaitable[XpConfig]]:
    async def _load() -> XpConfig:
        # XP min/max/cooldown remain on the legacy path — they are
        # scalar settings, not bindings, and Phase 2 does not migrate
        # them.  Only the announce-channel field flows through the
        # bindings arbitration helper (PR-7).
        from core.runtime.config_arbitration import get_xp_announce_channel

        mn = int(await db.get_setting(guild_id, XP_MIN, str(_XP_DEFAULT_MIN)))
        mx = int(await db.get_setting(guild_id, XP_MAX, str(_XP_DEFAULT_MAX)))
        cd = int(
            await db.get_setting(guild_id, XP_COOLDOWN, str(_XP_DEFAULT_COOLDOWN)),
        )
        ann_result = await get_xp_announce_channel(guild_id)
        ann = ann_result.value or ""
        return XpConfig(xp_min=mn, xp_max=mx, cooldown=cd, announce_channel=ann)

    return _load


_xp_config_accessor: TypedAccessor[XpConfig] = TypedAccessor(
    cache_key="xp_config",
    loader_factory=_xp_config_loader,
)


async def get_xp_config(guild_id: int) -> XpConfig:
    """Return cached XP config for ``guild_id``; load from DB on miss."""
    return await _xp_config_accessor.get(guild_id)


def invalidate_xp_config(guild_id: int) -> None:
    """Drop the cached XP config — call from every XP-setting admin write."""
    _xp_config_accessor.invalidate(guild_id)


# ---------------------------------------------------------------------------
# XP threshold roles — consumed by cogs/xp_cog.py + role assignment paths
# ---------------------------------------------------------------------------


def _xp_threshold_roles_loader(
    guild_id: int,
) -> Callable[[], Awaitable[list[dict]]]:
    async def _load() -> list[dict]:
        return await db.get_xp_threshold_roles(guild_id)

    return _load


_xp_threshold_roles_accessor: TypedAccessor[list[dict]] = TypedAccessor(
    cache_key="xp_threshold_roles",
    loader_factory=_xp_threshold_roles_loader,
)


async def get_xp_threshold_roles(guild_id: int) -> list[dict]:
    """Return cached XP→role threshold list for ``guild_id``; load on miss."""
    return await _xp_threshold_roles_accessor.get(guild_id)


def invalidate_xp_threshold_roles(guild_id: int) -> None:
    """Drop cached XP threshold roles — call from every role-threshold write."""
    _xp_threshold_roles_accessor.invalidate(guild_id)


__all__ = [
    "TypedAccessor",
    "XpConfig",
    "get_xp_config",
    "get_xp_threshold_roles",
    "invalidate_xp_config",
    "invalidate_xp_threshold_roles",
]
