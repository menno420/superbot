"""Settings keys owned by the Automod subsystem (cogs.automod_cog).

automod v1 (owner decision Q-0108): the automated message-filter layer beneath
manual moderation.  All keys are ordinary scalar guild settings (the legacy KV
``guild_settings`` table) — there is **no migration**.  Prefixed ``automod_*``
to keep the shared KV namespace collision-free, matching the per-subsystem
naming convention.

Every flag defaults OFF so a fresh guild behaves exactly as it does today; an
operator opts each rule in.  See ``services.automod_config`` for the defaults
(the single source of truth shared with ``cogs.automod.schemas``).
"""

# Master switch — when off, the stage is a no-op regardless of per-rule flags.
AUTOMOD_ENABLED = "automod_enabled"

# Per-rule enable flags (the four owner-approved v1 rule types, plus the
# cross-channel-spam + duplicate-content rules added 2026-07-07 — owner-raised
# gap: the original spam rule is rate-only and keyed per-channel, so it can't
# separate a burst of different messages from the same message repeated, and
# a burst spread across channels evades it entirely).
AUTOMOD_SPAM_ENABLED = "automod_spam_enabled"
AUTOMOD_INVITES_ENABLED = "automod_invites_enabled"
AUTOMOD_CAPS_ENABLED = "automod_caps_enabled"
AUTOMOD_MENTIONS_ENABLED = "automod_mentions_enabled"
AUTOMOD_CROSS_CHANNEL_SPAM_ENABLED = "automod_cross_channel_spam_enabled"
AUTOMOD_DUPLICATE_ENABLED = "automod_duplicate_enabled"

# Rule thresholds.
AUTOMOD_SPAM_COUNT = "automod_spam_count"  # messages within the window
AUTOMOD_SPAM_WINDOW_SECONDS = "automod_spam_window_seconds"
AUTOMOD_CAPS_PERCENT = "automod_caps_percent"  # uppercase % that trips the rule
AUTOMOD_MENTIONS_COUNT = "automod_mentions_count"  # @mentions in one message
AUTOMOD_CROSS_CHANNEL_SPAM_COUNT = "automod_cross_channel_spam_count"
AUTOMOD_DUPLICATE_COUNT = "automod_duplicate_count"  # same-content repeats

# Exempt safety valve — CSV of role/channel ids never acted on (staff,
# announcement channels, …).  Parsed by services.automod_config.
AUTOMOD_EXEMPT_ROLES = "automod_exempt_roles"
AUTOMOD_EXEMPT_CHANNELS = "automod_exempt_channels"
