"""Settings keys owned by the AI Platform subsystem (cogs.ai_cog).

M1 of the BTD6-top-level + AI-central-policy initiative. These scalars
are the first AI-owned guild settings. M2 introduces typed AI policy
tables (`ai_guild_policy` et al.) and backfills these scalars into
them; from M2 onward the typed tables are the runtime source of
truth and the scalars become a presentation / backcompat surface.
"""

AI_ENABLED = "ai_enabled"
AI_NATURAL_LANGUAGE_ENABLED = "ai_natural_language_enabled"
AI_DEFAULT_PROVIDER = "ai_default_provider"
AI_DEFAULT_MODEL = "ai_default_model"
AI_MINIMUM_LEVEL_DEFAULT = "ai_minimum_level_default"
AI_COOLDOWN_SECONDS = "ai_cooldown_seconds"
AI_FRESH_USER_MENTION_ALLOWANCE = "ai_fresh_user_mention_allowance"
AI_GUILD_INSTRUCTION_PROFILE = "ai_guild_instruction_profile"

# Chat memory (off by default).
# AI_MEMORY_WINDOW_MINUTES: 0 disables the time-window memory; the bot
# still keeps the last ``MIN_FLOOR`` (3) messages per channel as a
# minimum so a basic conversational handle survives without operator
# config. Hard cap 120 minutes.
AI_MEMORY_WINDOW_MINUTES = "ai_memory_window_minutes"

# When True and the in-process cache holds fewer turns than the
# configured window's floor, the natural-language stage scans the
# channel's recent Discord history to backfill. When False the
# memory is limited strictly to messages observed since process start.
AI_MEMORY_CHANNEL_SCAN_ENABLED = "ai_memory_channel_scan_enabled"

# The dedicated channel where AI "didn't-know" outcomes + user corrections are
# posted for review (services/ai_review_log_service.py → cogs/ai_review_cog.py).
# Unset = no channel feed; the queryable `!aireview` log still records everything.
AI_REVIEW_CHANNEL = "ai_review_channel"
