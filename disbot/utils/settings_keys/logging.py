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

# ---------------------------------------------------------------------------
# Server event logging v2 — Discord audit-log integration
# ---------------------------------------------------------------------------
#
# v1 (Q-0109) only heard five gateway events on non-bot subjects, so anything
# done via Discord's UI or another bot (a ban, a channel edit, a role rename)
# was invisible.  v2 adds a single ``on_audit_log_entry_create`` listener that
# maps Discord's audit-log actions to embeds — every administrative action, by
# anyone, with the actor named.  These four category flags gate the new groups;
# each is still gated by the master ``LOGGING_ENABLED`` switch *and* its own
# flag, and all default OFF so an existing guild is byte-identical until it opts
# a group in.
#
# * ``moderation`` — bans / unbans / kicks / timeouts / prunes / voice-kicks
#   (audit-log). Distinct from ``logging.mod_channel``, which only receives
#   actions taken *through SuperBot's own commands*; this catches the same
#   actions taken by anyone.
# * ``channels``   — channel + permission-overwrite create / delete / update.
# * ``server``     — guild settings, role definitions, emoji / sticker / webhook
#   / integration changes, and invite create / delete.
# * ``voice``      — voice-channel join / leave / move (passive gateway event,
#   ``on_voice_state_update`` — not audit-log-sourced).
#
# The existing ``roles`` category is repurposed to the audit-log path in v2 so
# it can finally name *who* granted/revoked the role (the phase-2 gap called out
# in docs/server-logging.md).
LOGGING_MODERATION_ENABLED = "logging_moderation_enabled"
LOGGING_CHANNELS_ENABLED = "logging_channels_enabled"
LOGGING_SERVER_ENABLED = "logging_server_enabled"
LOGGING_VOICE_ENABLED = "logging_voice_enabled"

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
