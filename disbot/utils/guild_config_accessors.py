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

Accessors land here as consumers migrate.  Phase S2.2 adds the XP
accessors; later cogs add their accessors here as they migrate off
``db.get_setting`` hot-path calls.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.runtime import guild_config
from utils import db
from utils.settings_keys import XP_ANNOUNCE_CHANNEL, XP_COOLDOWN, XP_MAX, XP_MIN

# ---------------------------------------------------------------------------
# XP listener config — consumed by cogs/xp_cog.py:on_message (S2.2)
# ---------------------------------------------------------------------------

# Defaults mirror the module-level constants in cogs/xp_cog.py.  They live
# here so the accessor is self-contained — the loader can compute the
# config without a circular import back into the cog.
_XP_DEFAULT_MIN: int = 15
_XP_DEFAULT_MAX: int = 25
_XP_DEFAULT_COOLDOWN: int = 60

_KEY_XP_CONFIG = "xp_config"
_KEY_XP_THRESHOLD_ROLES = "xp_threshold_roles"


@dataclass(frozen=True)
class XpConfig:
    """Cached XP-listener configuration for a single guild."""

    xp_min: int
    xp_max: int
    cooldown: int
    announce_channel: str  # "" when unset; cog interprets as "use source channel"


async def get_xp_config(guild_id: int) -> XpConfig:
    """Return cached XP config for ``guild_id``; load from DB on miss."""

    async def _loader() -> XpConfig:
        mn = int(await db.get_setting(guild_id, XP_MIN, str(_XP_DEFAULT_MIN)))
        mx = int(await db.get_setting(guild_id, XP_MAX, str(_XP_DEFAULT_MAX)))
        cd = int(await db.get_setting(guild_id, XP_COOLDOWN, str(_XP_DEFAULT_COOLDOWN)))
        ann = await db.get_setting(guild_id, XP_ANNOUNCE_CHANNEL, "")
        return XpConfig(xp_min=mn, xp_max=mx, cooldown=cd, announce_channel=ann)

    return await guild_config.get(guild_id, _KEY_XP_CONFIG, loader=_loader)


def invalidate_xp_config(guild_id: int) -> None:
    """Drop the cached XP config — call from every XP-setting admin write."""
    guild_config.invalidate(guild_id, _KEY_XP_CONFIG)


async def get_xp_threshold_roles(guild_id: int) -> list[dict]:
    """Return cached XP→role threshold list for ``guild_id``; load on miss."""

    async def _loader() -> list[dict]:
        return await db.get_xp_threshold_roles(guild_id)

    return await guild_config.get(
        guild_id,
        _KEY_XP_THRESHOLD_ROLES,
        loader=_loader,
    )


def invalidate_xp_threshold_roles(guild_id: int) -> None:
    """Drop cached XP threshold roles — call from every role-threshold write."""
    guild_config.invalidate(guild_id, _KEY_XP_THRESHOLD_ROLES)


__all__ = [
    "XpConfig",
    "get_xp_config",
    "get_xp_threshold_roles",
    "invalidate_xp_config",
    "invalidate_xp_threshold_roles",
]
