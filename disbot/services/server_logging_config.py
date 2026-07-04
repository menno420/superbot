"""Event-logging policy — the config read model for server event logging v1.

Server event logging (owner decision Q-0109): the passive layer of
:mod:`services.server_logging` that posts an embed when a tracked Discord
event happens — message edits/deletions, member joins/leaves, and role
grants/revocations.  Mirrors :mod:`services.automod_config` and
:mod:`services.moderation_config` exactly: the behaviour is loaded **once**
into a frozen read model so the cog listeners share identical config
resolution.

This module owns:

* the canonical **default constants** (one source of truth shared by the
  :class:`SettingSpec` declarations in ``cogs/logging/schemas.py`` and by
  :func:`load_policy`'s fallbacks);
* :class:`EventLoggingPolicy`, the frozen read model;
* :func:`load_policy`, which composes the typed values via
  :func:`services.settings_resolution.resolve_value`.

The settings are stored as ordinary scalar guild settings (the legacy KV
table); there is **no migration** — the keys live in
:mod:`utils.settings_keys.logging` and are operator-editable through the
existing ``!settings`` widget dispatcher.  The master switch is the
existing ``logging.enabled`` flag (the same one
:func:`services.server_logging.is_enabled` reads), so a guild that already
runs moderation-action logging keeps one master switch for everything.

Cycle discipline (mirrors :mod:`services.automod_config`): the only
cross-package import (``settings_resolution``) is function-local; top-level
imports are stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SUBSYSTEM = "logging"

# ---------------------------------------------------------------------------
# Event categories — the three Q-0109 groups.  Each maps to one logging
# route kind (see ``services.server_logging._CATEGORY_TO_ROUTE``).
# ---------------------------------------------------------------------------

CATEGORY_MESSAGES = "messages"  # message edits + deletions (passive gateway)
CATEGORY_MEMBERS = "members"  # member joins + leaves (passive gateway)
CATEGORY_ROLES = "roles"  # member role grants + revocations (audit-log in v2)
# -- Server event logging v2 (Discord audit-log integration) ----------------
CATEGORY_MODERATION = "moderation"  # ban/unban/kick/timeout/prune (audit-log)
CATEGORY_CHANNELS = "channels"  # channel + overwrite changes (audit-log)
CATEGORY_SERVER = "server"  # guild/roles-defs/emoji/webhook/invite (audit-log)
CATEGORY_VOICE = "voice"  # voice join/leave/move (passive gateway)

CATEGORIES: tuple[str, ...] = (
    CATEGORY_MESSAGES,
    CATEGORY_MEMBERS,
    CATEGORY_ROLES,
    CATEGORY_MODERATION,
    CATEGORY_CHANNELS,
    CATEGORY_SERVER,
    CATEGORY_VOICE,
)

# ---------------------------------------------------------------------------
# Routing modes.  ``combined`` sends every category to one channel;
# ``per_category`` sends each to its own (falling back to the combined
# events channel when a category channel is unset).  The owner-configurable
# Q-0109 choice — ``mock_logging_routing`` renders both.
# ---------------------------------------------------------------------------

ROUTING_COMBINED = "combined"
ROUTING_PER_CATEGORY = "per_category"
VALID_ROUTING: frozenset[str] = frozenset({ROUTING_COMBINED, ROUTING_PER_CATEGORY})

# ---------------------------------------------------------------------------
# Canonical defaults — the single source of truth.
#
# ``cogs/logging/schemas.py`` imports these for its SettingSpec ``default=``
# values; :func:`load_policy` uses them as the ``resolve_value`` fallback, so
# a spec default and a policy default can never silently drift (pinned by the
# schema test).  Every category defaults OFF so a fresh guild — and a guild
# that already enables ``logging.enabled`` for moderation logging — behaves
# exactly as it does today.
# ---------------------------------------------------------------------------

DEFAULT_ENABLED = False  # master switch (the existing logging.enabled key)
DEFAULT_MESSAGES_ENABLED = False
DEFAULT_MEMBERS_ENABLED = False
DEFAULT_ROLES_ENABLED = False
# Server event logging v2 — new audit-log/voice categories, all OFF by default.
DEFAULT_MODERATION_ENABLED = False
DEFAULT_CHANNELS_ENABLED = False
DEFAULT_SERVER_ENABLED = False
DEFAULT_VOICE_ENABLED = False
DEFAULT_EVENT_ROUTING = ROUTING_COMBINED

# Exclusion lists (completion cert punch #1) — comma-separated id CSV,
# empty by default (no exclusion, so every existing guild is unchanged).
DEFAULT_IGNORED_CHANNELS = ""
DEFAULT_IGNORED_USERS = ""


@dataclass(frozen=True)
class EventLoggingPolicy:
    """Resolved event-logging behaviour for one guild.

    ``frozen`` so it can be cached/compared safely.  Every category is
    gated by both the master :attr:`enabled` flag and its own per-category
    flag — :meth:`should_log` is the single gate the handlers consult.
    """

    enabled: bool = DEFAULT_ENABLED
    messages_enabled: bool = DEFAULT_MESSAGES_ENABLED
    members_enabled: bool = DEFAULT_MEMBERS_ENABLED
    roles_enabled: bool = DEFAULT_ROLES_ENABLED
    # Server event logging v2 — audit-log-sourced + voice categories.
    moderation_enabled: bool = DEFAULT_MODERATION_ENABLED
    channels_enabled: bool = DEFAULT_CHANNELS_ENABLED
    server_enabled: bool = DEFAULT_SERVER_ENABLED
    voice_enabled: bool = DEFAULT_VOICE_ENABLED
    routing: str = DEFAULT_EVENT_ROUTING
    # Exclusion lists (completion cert punch #1). A passive event whose
    # channel id is in ``ignored_channel_ids`` or whose subject (author /
    # member) id is in ``ignored_user_ids`` is never logged, for every
    # category. Empty by default → no exclusion.
    ignored_channel_ids: frozenset[int] = field(default_factory=frozenset)
    ignored_user_ids: frozenset[int] = field(default_factory=frozenset)

    @property
    def per_category(self) -> bool:
        """True when each category routes to its own channel."""
        return self.routing == ROUTING_PER_CATEGORY

    @property
    def any_category_enabled(self) -> bool:
        """True when at least one category could log (still gated by ``enabled``)."""
        return any(
            (
                self.messages_enabled,
                self.members_enabled,
                self.roles_enabled,
                self.moderation_enabled,
                self.channels_enabled,
                self.server_enabled,
                self.voice_enabled,
            ),
        )

    def category_enabled(self, category: str) -> bool:
        """Return the per-category flag for ``category`` (False if unknown)."""
        return {
            CATEGORY_MESSAGES: self.messages_enabled,
            CATEGORY_MEMBERS: self.members_enabled,
            CATEGORY_ROLES: self.roles_enabled,
            CATEGORY_MODERATION: self.moderation_enabled,
            CATEGORY_CHANNELS: self.channels_enabled,
            CATEGORY_SERVER: self.server_enabled,
            CATEGORY_VOICE: self.voice_enabled,
        }.get(category, False)

    def should_log(self, category: str) -> bool:
        """The single gate: master switch ON **and** the category enabled."""
        return self.enabled and self.category_enabled(category)

    def is_ignored(
        self,
        *,
        channel_id: int | None = None,
        user_id: int | None = None,
    ) -> bool:
        """Return True when this event's channel or subject is excluded.

        The exclusion gate applied *after* :meth:`should_log`: a passive
        event is suppressed when its originating channel is in
        :attr:`ignored_channel_ids` **or** its subject (message author /
        joining-leaving member / role-changed member) is in
        :attr:`ignored_user_ids`.  ``None`` ids (e.g. a channel-less
        member event) never match, so a category with no channel context
        is only ever filtered by the user list.
        """
        if channel_id is not None and channel_id in self.ignored_channel_ids:
            return True
        return user_id is not None and user_id in self.ignored_user_ids


async def load_policy(guild_id: int) -> EventLoggingPolicy:
    """Load the effective :class:`EventLoggingPolicy` for ``guild_id``.

    Each field resolves through :func:`services.settings_resolution.resolve_value`
    so coercion, validation, and provenance stay centralised; a missing or
    malformed stored value transparently falls back to the canonical
    default.  An unrecognised routing token also degrades to the default
    (``combined``) rather than disabling routing.
    """
    from services.automod_config import parse_id_csv
    from services.settings_resolution import resolve_value

    enabled = await resolve_value(guild_id, SUBSYSTEM, "enabled", DEFAULT_ENABLED)
    messages_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "messages_enabled",
        DEFAULT_MESSAGES_ENABLED,
    )
    members_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "members_enabled",
        DEFAULT_MEMBERS_ENABLED,
    )
    roles_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "roles_enabled",
        DEFAULT_ROLES_ENABLED,
    )
    moderation_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "moderation_enabled",
        DEFAULT_MODERATION_ENABLED,
    )
    channels_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "channels_enabled",
        DEFAULT_CHANNELS_ENABLED,
    )
    server_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "server_enabled",
        DEFAULT_SERVER_ENABLED,
    )
    voice_enabled = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "voice_enabled",
        DEFAULT_VOICE_ENABLED,
    )
    routing = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "event_routing",
        DEFAULT_EVENT_ROUTING,
    )
    if routing not in VALID_ROUTING:
        routing = DEFAULT_EVENT_ROUTING
    ignored_channels_raw = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "ignored_channels",
        DEFAULT_IGNORED_CHANNELS,
    )
    ignored_users_raw = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "ignored_users",
        DEFAULT_IGNORED_USERS,
    )

    return EventLoggingPolicy(
        enabled=enabled,
        messages_enabled=messages_enabled,
        members_enabled=members_enabled,
        roles_enabled=roles_enabled,
        moderation_enabled=moderation_enabled,
        channels_enabled=channels_enabled,
        server_enabled=server_enabled,
        voice_enabled=voice_enabled,
        routing=routing,
        ignored_channel_ids=parse_id_csv(ignored_channels_raw),
        ignored_user_ids=parse_id_csv(ignored_users_raw),
    )


__all__ = [
    "CATEGORIES",
    "CATEGORY_CHANNELS",
    "CATEGORY_MEMBERS",
    "CATEGORY_MESSAGES",
    "CATEGORY_MODERATION",
    "CATEGORY_ROLES",
    "CATEGORY_SERVER",
    "CATEGORY_VOICE",
    "DEFAULT_CHANNELS_ENABLED",
    "DEFAULT_EVENT_ROUTING",
    "DEFAULT_IGNORED_CHANNELS",
    "DEFAULT_IGNORED_USERS",
    "DEFAULT_MEMBERS_ENABLED",
    "DEFAULT_MESSAGES_ENABLED",
    "DEFAULT_MODERATION_ENABLED",
    "DEFAULT_ROLES_ENABLED",
    "DEFAULT_SERVER_ENABLED",
    "DEFAULT_VOICE_ENABLED",
    "EventLoggingPolicy",
    "ROUTING_COMBINED",
    "ROUTING_PER_CATEGORY",
    "VALID_ROUTING",
    "load_policy",
]
