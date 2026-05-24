# config.py - Clean and optimized version
import os

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ==========================
# Database
# ==========================
# Required: postgres://user:password@host:5432/dbname
# Set via DATABASE_URL environment variable (Railway / Render standard).
# db.py will raise a clear RuntimeError at startup if this is missing.

# ==========================
# Discord Bot Token
# ==========================
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN_PRODUCTION")

# Ensure the token is properly loaded
if not DISCORD_BOT_TOKEN or DISCORD_BOT_TOKEN.strip() == "":
    raise ValueError("ERROR: DISCORD_BOT_TOKEN is missing or empty!")

# ==========================
# Bot Prefix
# ==========================
PREFIX = os.getenv("BOT_PREFIX", "!")

# ==========================
# Initial Cogs (Extensions)
# ==========================
INITIAL_EXTENSIONS = [
    # bootstrap_access_cog MUST load first: it replaces the legacy
    # `_channel_guard` defined in bot1.py with a fresh-guild-aware guard
    # so guild operators can run !help / !setup / !platform / !diagnostics /
    # !adminmenu / !settings / !syncslash before BOT_ALLOWED_CHANNELS is
    # configured. Reordering this entry breaks fresh-guild onboarding.
    "cogs.bootstrap_access_cog",
    "cogs.admin_cog",
    "cogs.help_cog",
    "cogs.role_cog",
    "cogs.moderation_cog",
    "cogs.xp_cog",
    "cogs.blackjack_cog",
    "cogs.rps_tournament_cog",
    "cogs.utility_cog",
    "cogs.cleanup_cog",
    "cogs.channel_cog",
    "cogs.inventory_cog",
    "cogs.economy_cog",
    "cogs.counting_cog",
    "cogs.deathmatch_cog",
    "cogs.proof_channel_cog",
    "cogs.mining_cog",
    "cogs.diagnostic_cog",
    "cogs.ai_cog",
    "cogs.chain_cog",
    "cogs.general_cog",
    "cogs.leaderboard_cog",
    "cogs.settings_cog",
    "cogs.logging_cog",
    "cogs.games_cog",
    "cogs.community_cog",
    "cogs.setup_cog",
]

# ==========================
# Webhook URL (for logs + startup notification)
# ==========================
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


# ==========================
# Channel Restrictions
# ==========================
def _parse_channel_ids(env_key: str, fallback: list[int]) -> set[int]:
    raw = os.getenv(env_key, "")
    if raw.strip():
        try:
            return {int(c.strip()) for c in raw.split(",") if c.strip()}
        except ValueError:
            pass
    return set(fallback)


# Channels where bot commands are allowed
ALLOWED_CHANNELS: set[int] = _parse_channel_ids(
    "BOT_ALLOWED_CHANNELS",
    [1348795460948590622, 1403818013408624642],
)

# Channels exempt from the cleanup cog's command-deletion rule
CLEANUP_WHITELIST_CHANNELS: set[int] = _parse_channel_ids(
    "BOT_CLEANUP_WHITELIST",
    [
        1348795460948590622,
        1349693768365903912,
        1349851456509055047,
        1403818013408624642,
    ],
)


# ==========================
# Setup-wizard advisor (Phase 9f / Track 5)
# ==========================
# Provider for the AI-assisted setup advisor. One of:
#   * ``deterministic`` — name-matching rules only (default).
#   * ``openai``        — OpenAI gpt-4o-mini behind strict JSON schema.
#                          Requires ``OPENAI_API_KEY``.
#   * ``anthropic``     — Claude Sonnet / Haiku. Requires ``ANTHROPIC_API_KEY``.
#                          Reserved; concrete adapter ships in a follow-up.
# When the requested provider is unavailable (missing key, missing SDK),
# the factory falls back to ``deterministic`` so CI / dev envs never make
# external calls by accident.
SETUP_ADVISOR_PROVIDER = os.getenv("SETUP_ADVISOR_PROVIDER", "deterministic").lower()
SETUP_ADVISOR_OPENAI_MODEL = os.getenv("SETUP_ADVISOR_OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ==========================
# AI platform (core/runtime/ai/gateway.py)
# ==========================
# ``AI_ENABLED``           — global on/off switch. Default off so the
#                            gateway is boot-safe in dev/CI and
#                            never makes external calls by accident.
# ``AI_DEFAULT_PROVIDER``  — provider name for tasks that do not
#                            override it. One of ``deterministic`` /
#                            ``openai``. Default ``deterministic``.
# Per-task overrides use ``AI_TASK_<NAME>_ENABLED`` and
# ``AI_ROUTING_<NAME>=<provider>:<model>``; consult
# ``core.runtime.ai.feature_flags`` / ``core.runtime.ai.routing``.
# ``SETUP_ADVISOR_PROVIDER`` remains the authoritative env var for
# the setup advisor's provider choice (back-compat).
AI_ENABLED = os.getenv("AI_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
AI_DEFAULT_PROVIDER = os.getenv("AI_DEFAULT_PROVIDER", "deterministic").lower()
