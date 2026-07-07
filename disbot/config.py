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
# Bot owner / operator
# ==========================
# The single Discord user authorised to administer this bot — the "bot
# owner" / code editor. Identity is established by the authoritative
# Discord user id (``message.author.id``), never by message text, so it
# cannot be spoofed by someone merely claiming to be the owner. Hardcoded
# default; overridable per-deployment via the ``BOT_OWNER_USER_ID`` env var.
try:
    BOT_OWNER_USER_ID: int | None = int(
        os.getenv("BOT_OWNER_USER_ID", "340415158583296000"),
    )
except ValueError:
    BOT_OWNER_USER_ID = None


def _parse_extra_owner_ids(raw: str) -> frozenset[int]:
    """Parse ``EXTRA_OWNER_USER_IDS`` (comma/semicolon-separated Discord user
    ids) into a frozenset, silently dropping malformed tokens — a typo in the
    env var must never crash boot (config is imported by everything)."""
    ids: set[int] = set()
    for token in raw.replace(";", ",").split(","):
        token = token.strip()
        if not token:
            continue
        try:
            ids.add(int(token))
        except ValueError:
            continue
    return frozenset(ids)


# Additional fully-trusted operator accounts (owner ruling Q-0245) — e.g. the
# owner's second/test account used to exercise moderator functions live.
# Every id listed here clears BOTH owner seams (``is_platform_owner`` below
# and ``bot.is_owner`` via the bot1 subclass), in EVERY guild — treat these
# accounts' credentials exactly like the main owner account's. Deploy-time
# env var, never hardcoded in source; empty default grants nothing.
EXTRA_OWNER_USER_IDS: frozenset[int] = _parse_extra_owner_ids(
    os.getenv("EXTRA_OWNER_USER_IDS", ""),
)


def is_platform_owner(user_id: int | None) -> bool:
    """True iff ``user_id`` is the deploy-declared bot/platform owner.

    The single source of truth for "is this the bot owner?".  The platform
    owner is :data:`BOT_OWNER_USER_ID` — the ``PermissionTier.PLATFORM_OWNER``
    deploy-time allowlist (see :mod:`governance.permission_tiers`).  Identity
    is the authoritative Discord user id (``message.author.id`` /
    ``interaction.user.id``), never message text, so it cannot be spoofed.

    The configured owner holds **full bot-configuration authority in every
    guild they are a member of**, even without Discord permissions there — so
    they can always set the bot up correctly (AI policy, command channels,
    setup, settings) regardless of their server role.  Every authority seam
    (governance capability/visibility, the service mutation gates, setup
    access, and the view admin gates) routes its owner check through here so
    the rule lives in exactly one place.  ``config`` is a layer-free leaf
    module importable from every layer, so callers in ``governance`` /
    ``services`` / ``views`` all share this one definition.

    Returns ``False`` for ``None`` and when no owner is configured
    (``BOT_OWNER_USER_ID is None``) so an unconfigured deployment grants no
    one elevated authority by accident.

    Accounts in :data:`EXTRA_OWNER_USER_IDS` (owner ruling Q-0245 — the
    owner's declared second/test account) are equivalent to the platform
    owner through this same single seam.
    """
    if user_id is None:
        return False
    if user_id in EXTRA_OWNER_USER_IDS:
        return True
    return BOT_OWNER_USER_ID is not None and user_id == BOT_OWNER_USER_ID


# ==========================
# Initial Cogs (Extensions)
# ==========================
INITIAL_EXTENSIONS = [
    # bootstrap_access_cog MUST load first: it installs the central
    # command-access guard (prefix + slash) that gates every command
    # invocation.  Reordering this entry would leave a window where
    # commands could be admitted before the policy resolver is wired
    # in.  See `docs/architecture.md` for the admission chain.
    "cogs.bootstrap_access_cog",
    "cogs.admin_cog",
    "cogs.help_cog",
    "cogs.role_cog",
    "cogs.role_grants_cog",
    "cogs.starboard_cog",
    "cogs.moderation_cog",
    "cogs.automod_cog",
    "cogs.image_moderation_cog",
    "cogs.xp_cog",
    "cogs.karma_cog",
    "cogs.blackjack_cog",
    "cogs.casino_cog",
    "cogs.rps_tournament_cog",
    "cogs.utility_cog",
    "cogs.cleanup_cog",
    "cogs.channel_cog",
    "cogs.inventory_cog",
    "cogs.economy_cog",
    "cogs.treasury_cog",
    "cogs.counting_cog",
    "cogs.deathmatch_cog",
    "cogs.proof_channel_cog",
    "cogs.mining_cog",
    "cogs.fishing_cog",
    "cogs.creature_cog",
    "cogs.creature_battle_cog",
    "cogs.farm_cog",
    "cogs.diagnostic_cog",
    "cogs.health_maintenance_cog",
    "cogs.ai_cog",
    "cogs.ai_review_cog",
    "cogs.media_maintenance_cog",
    "cogs.btd6_cog",
    "cogs.btd6_reference_cog",
    "cogs.btd6_events_cog",
    "cogs.btd6_strategy_cog",
    "cogs.paragon_cog",
    "cogs.project_moon_cog",
    "cogs.btd6_ops_cog",
    "cogs.chain_cog",
    "cogs.general_cog",
    "cogs.four_twenty_cog",
    "cogs.leaderboard_cog",
    "cogs.settings_cog",
    "cogs.logging_cog",
    "cogs.games_cog",
    "cogs.community_cog",
    "cogs.community_spotlight_cog",
    "cogs.welcome_cog",
    "cogs.counters_cog",
    "cogs.ticket_cog",
    "cogs.security_cog",
    "cogs.setup_cog",
    "cogs.quicksetup_cog",
    "cogs.server_management_cog",
    "cogs.hermes_cog",
    "cogs.ux_lab_cog",
]

# ==========================
# Webhook URL (for logs + startup notification)
# ==========================
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


# ==========================
# Channel Restrictions
# ==========================
# Command admission (where prefix + slash commands are allowed) is
# owned by the per-guild ``guild_command_access_policy`` table
# (migration 050) and read through
# :func:`core.runtime.command_access.resolve_command_access`.  The
# pre-PR-7 ``BOT_ALLOWED_CHANNELS`` env var + hardcoded fallback
# channel IDs are gone; main-server channels are seeded by migration
# 051 so existing behavior is preserved.  Configure new guilds via
# ``!settings → Command access``.
#
# The cleanup cog's old ``CLEANUP_WHITELIST_CHANNELS`` env list (a
# remnant of an earlier bot version, hardcoded to dead old-server
# channels) was removed in favour of per-channel **cleanup policies**:
# to exempt a channel from command-style cleanup, set its policy to
# ``Off`` in the Cleanup Policies panel.


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

# ==========================
# BTD6 Paragon Calculator (services/paragon_service.py)
# ==========================
# External Paragon degree calculator API. The endpoint is public and CORS-open;
# an API key is optional (raises the rate limit from 60 to 300 req/min). When the
# host cannot reach the endpoint, ``paragon_service`` falls back to a local,
# clearly-labelled estimate computed from the documented formula.
PARAGON_API_BASE_URL = os.getenv(
    "PARAGON_API_BASE_URL",
    "https://paragon-calc.vercel.app",
)
PARAGON_API_KEY = os.getenv("PARAGON_API_KEY", "")

# ==========================
# BTD6 deterministic data source (services/btd6_data_service.py)
# ==========================
# Backend for the BTD6 fixture JSON + per-entity stats tree. See
# ``docs/btd6/btd6-data-backends.md``.
#   ""/"file"  → committed files under ``disbot/data/btd6/`` (default).
#   "postgres" → the ``btd6_data_blobs`` table (recommended when you already
#                run Postgres; seed with ``scripts/seed_btd6_data.py``). No new
#                infra / external dependency — reuses the bot's DB.
#   "cloud"    → a PUBLIC-READ object store / CDN at ``BTD6_DATA_BASE_URL``
#                (seed with ``scripts/upload_btd6_data.py``).
BTD6_DATA_BACKEND = os.getenv("BTD6_DATA_BACKEND", "")
# Cloud backend only: PUBLIC-READ base URL of the bucket/CDN. Setting this with
# no explicit BTD6_DATA_BACKEND still implies the cloud backend (back-compat).
BTD6_DATA_BASE_URL = os.getenv("BTD6_DATA_BASE_URL", "")
# Cloud backend only: local cache dir for fetched fixtures. Empty → a temp dir
# (ephemeral; re-warmed each boot).
BTD6_DATA_CACHE_DIR = os.getenv("BTD6_DATA_CACHE_DIR", "")
# Postgres backend only: auto-seed the ``btd6_data_blobs`` store from the deployed
# files on boot, so a data PR applies on deploy with no manual ``!btd6ops
# seed-data``. Default on; set to "0"/"false"/"no" to disable (kill-switch). A
# no-op for the file backend (reads bundled files directly) and the cloud backend
# (seeded via its own upload script).
BTD6_AUTO_SEED = os.getenv("BTD6_AUTO_SEED", "1")

# Startup auto-sync of the application-command tree: on boot, diff the bot's
# local slash tree against Discord's registered commands and ``tree.sync()`` only
# when they differ, so a command change (e.g. the BTD6 unification) goes live on
# deploy with no manual ``!syncslash``. Default on; set to "0"/"false"/"no"/"off"
# to disable (kill-switch). Failures are non-fatal. See
# ``services/command_tree_sync.py``.
AUTO_SYNC_COMMANDS = os.getenv("AUTO_SYNC_COMMANDS", "1")
