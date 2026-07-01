"""Settings keys owned by the server-logging service (services.server_logging).

These four keys live in the legacy ``guild_settings`` table.  All
default to OFF / empty so the service is inert on a fresh install
until an operator opts in.
"""

# Per-guild master switch.  String 'true' / 'false' / '1' / '0' — see
# :func:`services.server_logging.is_enabled` for the parse contract.
LOGGING_ENABLED = "logging_enabled"

# Channel id (str-of-int) for moderation action embeds.
LOGGING_MOD_CHANNEL = "logging_mod_channel"

# Channel id (str-of-int) for cleanup auto-delete embeds.  Falls back
# to the mod channel if unset.
LOGGING_CLEANUP_CHANNEL = "logging_cleanup_channel"

# When true and a configured channel id is missing/invalid, the
# service calls ``guild_resources.ensure_channel`` to create a
# fall-back channel named ``DEFAULT_LOG_CHANNEL_NAME``.
LOGGING_AUTO_CREATE_CHANNELS = "logging_auto_create_channels"

# Default channel name used by ``ensure_log_channel`` when
# auto-creation is enabled.
DEFAULT_MOD_CHANNEL_NAME = "bot-mod-log"
DEFAULT_CLEANUP_CHANNEL_NAME = "bot-cleanup-log"

# ---------------------------------------------------------------------------
# Server event logging v1 (Q-0109)
# ---------------------------------------------------------------------------
#
# Passive Discord-event logging — message edits/deletions, member
# joins/leaves, and role grants/revocations.  Each per-category flag is
# gated by the master ``LOGGING_ENABLED`` switch *and* its own flag, so a
# guild that has logging on for moderation actions sees no new behaviour
# until it opts a category in.  All default OFF — a fresh guild is
# unchanged.  Stored in the same legacy ``guild_settings`` KV table; **no
# migration**.  Resolved through the ``logging`` subsystem read model in
# :mod:`services.server_logging_config`.

# Per-category enable flags.
LOGGING_MESSAGES_ENABLED = "logging_messages_enabled"
LOGGING_MEMBERS_ENABLED = "logging_members_enabled"
LOGGING_ROLES_ENABLED = "logging_roles_enabled"

# Channel routing layout: ``"combined"`` (every category to one channel)
# or ``"per_category"`` (each category to its own channel, falling back to
# the combined events channel when a category channel is unset).  The
# owner-configurable choice from Q-0109; the ``mock_logging_routing`` UX
# exhibit renders both modes.
LOGGING_EVENT_ROUTING = "logging_event_routing"

# Exclusion lists (Logging completion cert punch #1) — comma-separated id
# CSV.  A passive event whose *channel* id is in ``LOGGING_IGNORED_CHANNELS``
# or whose *subject* (author/member) id is in ``LOGGING_IGNORED_USERS`` is
# never logged, for every category.  Both default empty (no exclusion), so a
# fresh guild — and every existing guild — behaves exactly as before.  The
# parse is tolerant (bad tokens dropped); the write-time validator is loud.
LOGGING_IGNORED_CHANNELS = "logging_ignored_channels"
LOGGING_IGNORED_USERS = "logging_ignored_users"

# Default channel names used by ``ensure_log_channel`` for the new event
# routes when auto-creation is enabled.
DEFAULT_EVENTS_CHANNEL_NAME = "bot-event-log"
DEFAULT_MESSAGE_LOG_CHANNEL_NAME = "bot-message-log"
DEFAULT_MEMBER_LOG_CHANNEL_NAME = "bot-member-log"
DEFAULT_ROLE_LOG_CHANNEL_NAME = "bot-role-log"
