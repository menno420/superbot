"""Karma policy — the config read model for the karma subsystem.

Mirrors :mod:`services.automod_config`: the operator-tunable behaviour is
loaded once into a frozen read model so the service and any future caller
share identical config resolution.  This module owns:

* the canonical **default constants** (one source of truth shared by the
  :class:`SettingSpec` declarations in ``cogs/karma/schemas.py`` and by
  :func:`load_policy`'s fallbacks);
* :class:`KarmaPolicy`, the frozen read model;
* :func:`load_policy`, which composes the typed values via
  :func:`services.settings_resolution.resolve_value`.

The settings are stored as ordinary scalar guild settings (the legacy KV
table); the keys live in :mod:`utils.settings_keys.karma` and are
operator-editable through the existing ``!settings`` widget.

Cycle discipline (mirrors :mod:`services.automod_config`): the only
cross-package import (``settings_resolution``) is function-local; top-level
imports are stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

SUBSYSTEM = "karma"

# ---------------------------------------------------------------------------
# Canonical defaults — the single source of truth.
#
# ``cogs/karma/schemas.py`` imports these for its SettingSpec ``default=``
# values and validator bounds; :func:`load_policy` uses them as the
# ``resolve_value`` fallback, so a spec default and a policy default can
# never silently drift (pinned by the schema test).
# ---------------------------------------------------------------------------

DEFAULT_ENABLED = True  # karma is a friendly, opt-out feature

# Per-(giver -> receiver) cooldown: a giver may thank the same recipient at
# most once per this many seconds (1 hour).  The primary anti-farm guard.
DEFAULT_COOLDOWN_SECONDS = 3600
MIN_COOLDOWN_SECONDS = 0
MAX_COOLDOWN_SECONDS = 604800  # one week

# Per-giver daily cap: total grants one account can mint per rolling 24h.
DEFAULT_DAILY_CAP = 10
MIN_DAILY_CAP = 1
MAX_DAILY_CAP = 1000

# React-to-thank trigger emoji: when set, reacting with this emoji on a
# message grants karma to that message's author (through the same audited
# service seam, so the cooldown + daily cap + self-give guard all apply).
# The empty string means the feature is OFF — the safe, byte-identical
# default, so no existing guild's reactions ever silently mint karma.
DEFAULT_REACTION_EMOJI = ""
MAX_REACTION_EMOJI_LEN = 64  # a unicode emoji or a <:name:id> custom form


@dataclass(frozen=True)
class KarmaPolicy:
    """Resolved karma behaviour for one guild.

    ``frozen`` so it can be cached/compared safely.
    """

    enabled: bool = DEFAULT_ENABLED
    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS
    daily_cap: int = DEFAULT_DAILY_CAP
    reaction_emoji: str = DEFAULT_REACTION_EMOJI


async def load_policy(guild_id: int) -> KarmaPolicy:
    """Load the effective :class:`KarmaPolicy` for ``guild_id``.

    Each field resolves through :func:`services.settings_resolution.resolve_value`
    so coercion, validation, and provenance stay centralised; a missing or
    malformed stored value transparently falls back to the canonical default.
    """
    from services.settings_resolution import resolve_value

    enabled = await resolve_value(guild_id, SUBSYSTEM, "enabled", DEFAULT_ENABLED)
    cooldown_seconds = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "cooldown_seconds",
        DEFAULT_COOLDOWN_SECONDS,
    )
    daily_cap = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "daily_cap",
        DEFAULT_DAILY_CAP,
    )
    reaction_emoji = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "reaction_emoji",
        DEFAULT_REACTION_EMOJI,
    )
    return KarmaPolicy(
        enabled=enabled,
        cooldown_seconds=cooldown_seconds,
        daily_cap=daily_cap,
        reaction_emoji=reaction_emoji,
    )
