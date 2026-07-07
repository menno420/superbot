"""Automod policy — the config read model for the automod message stage.

automod v1 (owner decision Q-0108): the automated filter layer beneath manual
moderation.  Mirrors :mod:`services.moderation_config` exactly — the behaviour
is loaded **once** into a frozen read model so the pipeline stage and any future
caller share identical config resolution.  This module owns:

* the canonical **default constants** (one source of truth shared by the
  :class:`SettingSpec` declarations in ``cogs/automod/schemas.py`` and by
  :func:`load_policy`'s fallbacks);
* :class:`AutomodPolicy`, the frozen read model;
* :func:`load_policy`, which composes the typed values via
  :func:`services.settings_resolution.resolve_value`.

The settings are stored as ordinary scalar guild settings (the legacy KV
table); there is **no migration** — the keys live in
:mod:`utils.settings_keys.automod` and are operator-editable through the
existing ``!settings`` widget dispatcher.

Cycle discipline (mirrors :mod:`services.moderation_config`): the only
cross-package import (``settings_resolution``) is function-local; top-level
imports are stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

SUBSYSTEM = "automod"

# ---------------------------------------------------------------------------
# Canonical defaults — the single source of truth.
#
# ``cogs/automod/schemas.py`` imports these for its SettingSpec ``default=``
# values and validator bounds; :func:`load_policy` uses them as the
# ``resolve_value`` fallback.  A spec default and a policy default can
# therefore never silently drift (pinned by the schema test).
#
# Every flag defaults OFF so a fresh guild behaves exactly as it does today.
# ---------------------------------------------------------------------------

DEFAULT_ENABLED = False  # master switch
DEFAULT_SPAM_ENABLED = False
DEFAULT_INVITES_ENABLED = False
DEFAULT_CAPS_ENABLED = False
DEFAULT_MENTIONS_ENABLED = False
DEFAULT_CROSS_CHANNEL_SPAM_ENABLED = False
DEFAULT_DUPLICATE_ENABLED = False

# Spam burst: N messages from one author in one channel within T seconds.
DEFAULT_SPAM_COUNT = 5
DEFAULT_SPAM_WINDOW_SECONDS = 7
MIN_SPAM_COUNT = 2
MAX_SPAM_COUNT = 50
MIN_SPAM_WINDOW_SECONDS = 1
MAX_SPAM_WINDOW_SECONDS = 120

# Cross-channel spam burst: N messages from one author across ANY channels in
# the same guild within the same spam window (a raid pattern the per-channel
# rule structurally cannot see, since its window is scoped per-channel).
# Defaults lower than the per-channel count — spreading across channels is a
# stronger raid signal than the same volume in one channel.
DEFAULT_CROSS_CHANNEL_SPAM_COUNT = 4
MIN_CROSS_CHANNEL_SPAM_COUNT = 2
MAX_CROSS_CHANNEL_SPAM_COUNT = 50

# Repeated/duplicate content: N messages with the same normalized content from
# one author (any channel) within the spam window — distinct from spam burst,
# which is pure rate and blind to what the messages actually say.
DEFAULT_DUPLICATE_COUNT = 3
MIN_DUPLICATE_COUNT = 2
MAX_DUPLICATE_COUNT = 50

# Excessive caps: trips when >= this percentage of the *letters* are uppercase.
DEFAULT_CAPS_PERCENT = 70
MIN_CAPS_PERCENT = 1
MAX_CAPS_PERCENT = 100
# Short shouts ("OK", "NO") are not spam — the caps rule only applies to
# messages with at least this many letters.  A constant, not a setting (v1).
MIN_CAPS_MESSAGE_LENGTH = 10

# Mass mentions: trips when a single message has >= this many user/role mentions.
DEFAULT_MENTIONS_COUNT = 4
MIN_MENTIONS_COUNT = 2
MAX_MENTIONS_COUNT = 50

# Exempt safety valve — CSV of ids never acted on.
DEFAULT_EXEMPT_ROLES = ""
DEFAULT_EXEMPT_CHANNELS = ""


@dataclass(frozen=True)
class AutomodPolicy:
    """Resolved automod behaviour for one guild.

    ``frozen`` so it can be cached/compared safely; the exempt collections are
    ``frozenset`` for the same reason.  Every rule is gated by both the master
    :attr:`enabled` flag and its own per-rule flag.
    """

    enabled: bool = DEFAULT_ENABLED
    spam_enabled: bool = DEFAULT_SPAM_ENABLED
    invites_enabled: bool = DEFAULT_INVITES_ENABLED
    caps_enabled: bool = DEFAULT_CAPS_ENABLED
    mentions_enabled: bool = DEFAULT_MENTIONS_ENABLED
    cross_channel_spam_enabled: bool = DEFAULT_CROSS_CHANNEL_SPAM_ENABLED
    duplicate_enabled: bool = DEFAULT_DUPLICATE_ENABLED
    spam_count: int = DEFAULT_SPAM_COUNT
    spam_window_seconds: int = DEFAULT_SPAM_WINDOW_SECONDS
    caps_percent: int = DEFAULT_CAPS_PERCENT
    mentions_count: int = DEFAULT_MENTIONS_COUNT
    cross_channel_spam_count: int = DEFAULT_CROSS_CHANNEL_SPAM_COUNT
    duplicate_count: int = DEFAULT_DUPLICATE_COUNT
    exempt_role_ids: frozenset[int] = frozenset()
    exempt_channel_ids: frozenset[int] = frozenset()

    @property
    def any_rule_enabled(self) -> bool:
        """True when at least one rule could act (still gated by ``enabled``)."""
        return (
            self.spam_enabled
            or self.invites_enabled
            or self.caps_enabled
            or self.mentions_enabled
            or self.cross_channel_spam_enabled
            or self.duplicate_enabled
        )


def parse_id_csv(raw: str) -> frozenset[int]:
    """Parse a comma-separated id string into a frozenset of ints.

    Tolerant: blanks and malformed tokens are skipped rather than raising, so a
    fat-fingered exempt list degrades to "fewer exemptions", never an error
    that would disable the policy load.
    """
    ids: set[int] = set()
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            ids.add(int(token))
        except ValueError:
            continue
    return frozenset(ids)


async def load_policy(guild_id: int) -> AutomodPolicy:
    """Load the effective :class:`AutomodPolicy` for ``guild_id``.

    Each field resolves through :func:`services.settings_resolution.resolve_value`
    so coercion, validation, and provenance stay centralised; a missing or
    malformed stored value transparently falls back to the canonical default.
    """
    from services.settings_resolution import resolve_value

    enabled = await resolve_value(guild_id, SUBSYSTEM, "enabled", DEFAULT_ENABLED)
    spam_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "spam_enabled",
        DEFAULT_SPAM_ENABLED,
    )
    invites_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "invites_enabled",
        DEFAULT_INVITES_ENABLED,
    )
    caps_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "caps_enabled",
        DEFAULT_CAPS_ENABLED,
    )
    mentions_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "mentions_enabled",
        DEFAULT_MENTIONS_ENABLED,
    )
    spam_count = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "spam_count",
        DEFAULT_SPAM_COUNT,
    )
    spam_window_seconds = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "spam_window_seconds",
        DEFAULT_SPAM_WINDOW_SECONDS,
    )
    caps_percent = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "caps_percent",
        DEFAULT_CAPS_PERCENT,
    )
    mentions_count = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "mentions_count",
        DEFAULT_MENTIONS_COUNT,
    )
    cross_channel_spam_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "cross_channel_spam_enabled",
        DEFAULT_CROSS_CHANNEL_SPAM_ENABLED,
    )
    cross_channel_spam_count = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "cross_channel_spam_count",
        DEFAULT_CROSS_CHANNEL_SPAM_COUNT,
    )
    duplicate_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "duplicate_enabled",
        DEFAULT_DUPLICATE_ENABLED,
    )
    duplicate_count = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "duplicate_count",
        DEFAULT_DUPLICATE_COUNT,
    )
    exempt_roles_raw = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "exempt_roles",
        DEFAULT_EXEMPT_ROLES,
    )
    exempt_channels_raw = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "exempt_channels",
        DEFAULT_EXEMPT_CHANNELS,
    )

    return AutomodPolicy(
        enabled=enabled,
        spam_enabled=spam_enabled,
        invites_enabled=invites_enabled,
        caps_enabled=caps_enabled,
        mentions_enabled=mentions_enabled,
        cross_channel_spam_enabled=cross_channel_spam_enabled,
        duplicate_enabled=duplicate_enabled,
        spam_count=spam_count,
        spam_window_seconds=spam_window_seconds,
        caps_percent=caps_percent,
        mentions_count=mentions_count,
        cross_channel_spam_count=cross_channel_spam_count,
        duplicate_count=duplicate_count,
        exempt_role_ids=parse_id_csv(exempt_roles_raw),
        exempt_channel_ids=parse_id_csv(exempt_channels_raw),
    )
