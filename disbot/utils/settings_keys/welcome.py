"""Settings keys owned by the Welcome subsystem (cogs.welcome_cog).

welcome v1 (owner decision Q-0110): greet members on join, optionally bid
farewell on leave, and optionally grant an entry role the moment a member
joins.  All keys are ordinary scalar guild settings (the legacy KV
``guild_settings`` table) — there is **no migration**.  Prefixed ``welcome_*``
to keep the shared KV namespace collision-free, matching the per-subsystem
naming convention.

Every flag defaults OFF (the master switch) or to the safe minimal shape so a
fresh guild behaves exactly as it does today; an operator opts welcome in and
sets the destination channel.  See ``services.welcome_config`` for the defaults
(the single source of truth shared with ``cogs.welcome.schemas``).
"""

# Master switch — when off, no greeting posts and no entry role is granted
# regardless of the per-event flags.
WELCOME_ENABLED = "welcome_enabled"

# Per-event flags.
WELCOME_JOIN_ENABLED = "welcome_join_enabled"  # post a greeting on join
WELCOME_LEAVE_ENABLED = "welcome_leave_enabled"  # post a farewell on leave

# Destination channel for the greeting/farewell embed — a channel id (str).
# Empty disables posting even when the per-event flags are on.
WELCOME_CHANNEL = "welcome_channel"

# Message templates — support the {user} / {server} / {count} placeholders.
WELCOME_JOIN_MESSAGE = "welcome_join_message"
WELCOME_LEAVE_MESSAGE = "welcome_leave_message"

# Optional entry role granted on join — a role id (str).  Empty grants none.
WELCOME_ENTRY_ROLE = "welcome_entry_role"

# Optional DM greeting — when on, the joining member is also sent the greeting
# as a direct message (in addition to / independent of the channel greeting).
# Off by default; needs no channel.  The DM body supports the same
# {user}/{server}/{count} placeholders and the same "---" random variants.
WELCOME_DM_ENABLED = "welcome_dm_enabled"
WELCOME_DM_MESSAGE = "welcome_dm_message"

# Welcome phase 2 (Q-0110): attach a rendered PIL greeting card to the join
# embed.  Off by default; degrades to embed-only when Pillow is unavailable.
WELCOME_CARD_ENABLED = "welcome_card_enabled"

# Join-delay age-gating (completion punch-list #2): skip greeting/DM/entry-role
# for a joining member whose account is younger than this many days (anti-raid).
# 0 disables it (every account greeted).
WELCOME_MIN_ACCOUNT_AGE_DAYS = "welcome_min_account_age_days"

# Ping-then-delete (completion punch-list #2): auto-delete the channel
# greeting/farewell message this many seconds after it posts.  0 keeps it.
WELCOME_DELETE_AFTER_SECONDS = "welcome_delete_after_seconds"
