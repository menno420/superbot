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
