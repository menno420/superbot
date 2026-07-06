"""Subsystem registry — immutable platform metadata manifest.

This file is the single source of truth for all subsystem definitions.
After validate_registry() runs at startup, every structure here is deep-frozen.
Overrides (visibility, cleanup rules) belong in governance DB, never here.

Capability namespace rule: {subsystem}.{resource}.{action} — three parts, enforced.
Reserved prefixes: _internal.*, system.*, governance.*

Optional metadata (Phase 1, schema v2):
    parent_hub: str | None — the key of a routable hub subsystem this entry
        belongs to (e.g. ``"games"``). When set, downstream UI code (Help
        filter, hubs) may treat the entry as a hub member. Two-hop chains
        (a parent_hub pointing at a subsystem that itself has parent_hub
        set) are rejected at validation time.
    hub_group: str | None — free-form visual grouping label (≤ 32 chars).
        Hubs use this to render sub-sections (e.g. ``"competitive"`` vs
        ``"activities"``); the rendering layer validates allowed values.

Phase 1 only introduces the *capability* — no existing entries set either
field. Assignments happen in Phase 3.

See services/governance_service.py for runtime policy resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from utils.ui_constants import (
    ADMIN_COLOR,
    CHANNEL_COLOR,
    ECONOMY_COLOR,
    GAME_COLOR,
    GENERAL_COLOR,
    MINING_COLOR,
    MOD_COLOR,
    ROLE_COLOR,
    UTILITY_COLOR,
)

# Incremented when subsystem content/metadata changes.
REGISTRY_VERSION = 1

# Incremented when the subsystem dict schema/shape itself changes.
# v2 (Phase 1): added optional ``parent_hub`` and ``hub_group`` fields.
REGISTRY_SCHEMA_VERSION = 2

# Maximum length of the optional ``hub_group`` label.
_HUB_GROUP_MAX_LEN = 32

# ---------------------------------------------------------------------------
# Subsystem manifest
# Immutable after validate_registry(). Do NOT mutate at runtime.
# ---------------------------------------------------------------------------

SUBSYSTEMS: dict[str, dict] = {
    "admin": {
        "display_name": "Administration",
        "description": "Cog management, server stats, diagnostics",
        "emoji": "⚙️",
        "color": ADMIN_COLOR.value,
        # Q-0074 (2026-06-10): administrator-visible placement, matching the
        # Admin hub's minimum_tier and the `!adminmenu` admission gate
        # (`has_permissions(administrator=True)`). The genuinely dangerous
        # actions (cog load/unload/reload, slash sync) keep their
        # `commands.is_owner()` execution checks — placement is display,
        # not admission.
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "admin",
        "tags": ["admin", "cogs", "management", "diagnostics"],
        "entry_points": ["adminmenu"],
        "default_channels": ["staff", "bot-spam"],
        "related_subsystems": ["diagnostic"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": True,
        "ui_priority": 90,
        "capabilities": [
            "admin.cog.load",
            "admin.cog.unload",
            "admin.cog.reload",
            "admin.server.stats",
        ],
    },
    # Key is snake_case (Q-0026): it must equal cog_name_to_subsystem(
    # "ServerManagementCog") = "server_management".  The ``servermanagement``
    # *entry_point* below is the prefix command name (``!servermanagement``),
    # which is a command identifier, not the subsystem key — they differ by
    # design, exactly like ``economy`` (key) vs ``economymenu`` (command).
    "server_management": {
        "display_name": "Server Management",
        "description": "Unified hub for moderation, channels, roles, cleanup, setup",
        "emoji": "🧭",
        "color": ADMIN_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "admin",
        "tags": ["admin", "hub", "navigation", "operations"],
        "entry_points": ["servermanagement"],
        "default_channels": ["staff", "bot-spam"],
        "related_subsystems": ["moderation", "cleanup"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        # The hub posts a navigation panel but owns no message-cleanup policy.
        "has_cleanup_rules": False,
        "ui_priority": 88,
        # Nested under the Server & Admin hub by the help-menu regrouping
        # (PR #1290): it is no longer a top-level Help section but remains a
        # full routing hub reachable as a child of Admin (and via
        # !servermanagement).
        "parent_hub": "admin",
        # Routing-only hub: it composes other subsystems' panels and holds no
        # capability of its own (authority is the administrator floor on the
        # command + the view's interaction_check).
        "capabilities": [],
    },
    "moderation": {
        "display_name": "Moderation",
        "description": "Warnings, timeouts, bans, mod logs",
        "emoji": "🔨",
        "color": MOD_COLOR.value,
        "visibility_tier": "moderator",
        "visibility_mode": "normal",
        "category": "moderation",
        "tags": ["moderation", "safety", "logs", "warn", "ban"],
        "entry_points": ["modmenu", "warn", "timeout", "kick", "ban", "unban"],
        "default_channels": ["staff", "mod-logs"],
        "related_subsystems": ["cleanup"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": True,
        "ui_priority": 80,
        "capabilities": [
            "moderation.warn.apply",
            "moderation.timeout.apply",
            "moderation.kick.apply",
            "moderation.ban.apply",
            "moderation.ban.remove",
            "moderation.log.view",
            "moderation.settings.configure",
        ],
    },
    "economy": {
        "display_name": "Economy",
        "description": "Daily coins, work, shop, balance",
        "emoji": "💰",
        "color": ECONOMY_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "economy",
        "tags": ["economy", "currency", "coins", "progression"],
        "entry_points": ["economymenu", "daily", "work", "balance"],
        "default_channels": ["economy", "bot-commands"],
        "related_subsystems": ["inventory", "mining"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": True,
        "ui_priority": 10,
        "capabilities": [
            "economy.currency.view",
            "economy.currency.earn",
            "economy.shop.browse",
            "economy.shop.buy",
            "economy.settings.configure",
        ],
    },
    "inventory": {
        "display_name": "Inventory",
        "description": "Item management and crafting",
        "emoji": "🎒",
        "color": ECONOMY_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "economy",
        "tags": ["inventory", "items", "crafting"],
        "entry_points": ["inventory"],
        "default_channels": ["economy", "bot-commands"],
        "related_subsystems": ["economy", "mining"],
        "dependencies": ["economy"],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 15,
        "parent_hub": "economy",
        "capabilities": [
            "inventory.item.view",
            "inventory.item.use",
            "inventory.craft.recipe",
        ],
    },
    # Server treasury (owner-directed task "treasury") — the bot's first
    # SERVER-OWNED (collective) coin pool, the seam between the per-user economy
    # and governance. Members contribute their own coins (a sink); server
    # managers disburse from the pool with `!treasury grant` (a manage_guild
    # gate). Homed under the Economy hub (a child, like inventory/leaderboard)
    # and reachable via the Help hook + `!treasury`. Soft-depends on economy
    # (it moves coins) but declares no HARD dependency so the panel still opens
    # (read-only) when the economy subsystem is disabled.
    "treasury": {
        "display_name": "Treasury",
        "description": "Server-owned coin pool — contribute coins; managers disburse",
        "emoji": "🏛️",
        "color": ECONOMY_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "economy",
        "tags": ["treasury", "economy", "coins", "governance"],
        "entry_points": ["treasury"],
        "default_channels": ["economy", "bot-commands"],
        "related_subsystems": ["economy", "inventory"],
        "dependencies": [],
        "soft_dependencies": ["economy"],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 16,
        "parent_hub": "economy",
        "capabilities": [
            "treasury.pool.view",
            "treasury.pool.contribute",
            "treasury.pool.disburse",
        ],
    },
    # Support tickets (owner-directed task "ticket") — a staff help-desk: a
    # member opens a private ticket channel (by command, by the launcher panel,
    # or via the AI in natural language); staff claim / add / remove / close it,
    # and closing posts a transcript. Homed under the Community hub (a child,
    # user tier, like xp/karma/roles), reachable via the Help hook + `!ticket`.
    "ticket": {
        "display_name": "Support Tickets",
        "description": "Private support tickets — open by command, panel, or the AI",
        "emoji": "🎫",
        "color": GENERAL_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "community",
        "tags": ["tickets", "support", "help", "staff"],
        "entry_points": ["ticket"],
        "default_channels": ["general", "bot-commands"],
        "related_subsystems": [],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 18,
        "parent_hub": "community",
        "capabilities": [
            "ticket.ticket.open",
            "ticket.ticket.manage",
            "ticket.config.update",
        ],
    },
    "mining": {
        "display_name": "Mining",
        "description": "Mining minigame and resource collection",
        "emoji": "⛏️",
        "color": MINING_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "economy",
        "tags": ["mining", "resources", "minigame"],
        "entry_points": ["minemenu", "mine"],
        "default_channels": ["mining", "bot-commands"],
        "related_subsystems": ["economy", "inventory"],
        "dependencies": ["economy"],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 20,
        "parent_hub": "games",
        "hub_group": "activities",
        "capabilities": [
            "mining.resource.mine",
            "mining.resource.view",
        ],
    },
    # Fishing minigame (ecosystem #2, PR 1 — the core loop). Deliberately
    # hub-less for PR 1 — surfaced via its Help hook (a static overview) +
    # the typed `!fish`/`!fishlog`/`!fishtop` commands, exactly like
    # `welcome`/`counters`. Folding `🎣 Fishing` into an actionable Games /
    # Explore-hub panel is a later plan slice
    # (docs/planning/fishing-open-world-expansion-plan-2026-06-18.md), at which point it
    # gains parent_hub + an actionable panel (the Games actionability contract).
    "fishing": {
        "display_name": "Fishing",
        "description": "Fishing minigame — cast a line, build your collection",
        "emoji": "🎣",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["fishing", "minigame", "activities"],
        "entry_points": ["fish", "fishlog"],
        "default_channels": ["games", "bot-commands"],
        "related_subsystems": ["mining"],
        # No hard dependency: fishing v1 writes only the catch log + game_xp
        # (no coins — fish value is a deferred owner question, Q-0175), so it must
        # not be locked out when an admin disables the economy subsystem.
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 21,
        "parent_hub": "games",
        "hub_group": "activities",
        "capabilities": [
            "fishing.catch.fish",
            "fishing.collection.view",
        ],
    },
    # Creature catch/collection game v1 (Q-0186/Q-0187,
    # docs/planning/creature-game-design-and-sim-2026-06-20.md). Homed under the
    # Games hub by the help-menu regrouping (PR #1290). The actionable in-panel
    # surface (the `!creatures` CreatureMenuView — catch / dex-browser / challenge /
    # ladder) shipped in the completion-first deepening run (Q-0209), closing the
    # certificate's hub-less rubric-B gap; `entry_points` now declares the full
    # command surface incl. the PvP commands (sibling creature_battle_cog).
    "creature": {
        "display_name": "Creatures",
        "description": "Catch original creatures and build your collection dex",
        "emoji": "🐾",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["creatures", "minigame", "activities"],
        "entry_points": [
            "creatures",
            "catch",
            "dex",
            "cbattle",
            "cbrecord",
            "cbattletop",
        ],
        "default_channels": ["games", "bot-commands"],
        "related_subsystems": ["fishing", "mining"],
        # No hard dependency: catching writes only the collection log + game_xp
        # (no coins), so it must not be locked out when the economy is disabled.
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 22,
        "parent_hub": "games",
        "hub_group": "activities",
        "capabilities": [
            "creature.catch.creature",
            "creature.collection.view",
        ],
    },
    # Idle egg/chicken farm (owner-directed task "Idle egg/chicken farm") — the
    # bot's first IDLE (accrue-over-time) game. Hens lay eggs over time (pure
    # `settle()` accrual, no ticker — ADR-001/002), collected for coins + game_xp;
    # coins buy more hens / a bigger coop. Homed under the Games hub (a child, like
    # mining/fishing/creature) and reachable via the Help hook, `!farm`, and the
    # Explore world hub. Soft-depends on economy (collect pays coins) but declares
    # no HARD dependency so it isn't locked out when the economy is disabled.
    "farm": {
        "display_name": "Chicken Farm",
        "description": "Idle egg farm — hens lay eggs over time; collect, sell, grow",
        "emoji": "🐔",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["farm", "idle", "chickens", "eggs", "activities"],
        "entry_points": ["farm"],
        "default_channels": ["games", "bot-commands"],
        "related_subsystems": ["economy", "mining", "fishing"],
        "dependencies": [],
        "soft_dependencies": ["economy"],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 23,
        "parent_hub": "games",
        "hub_group": "activities",
        "capabilities": [
            "farm.egg.collect",
            "farm.coop.manage",
        ],
    },
    "xp": {
        "display_name": "XP & Levels",
        "description": "Experience points, levels, and leaderboards",
        "emoji": "⭐",
        "color": ROLE_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "progression",
        "tags": ["xp", "levels", "progression", "leaderboard"],
        "entry_points": ["xpmenu", "rank"],
        "default_channels": ["bot-commands", "general"],
        "related_subsystems": ["role", "leaderboard"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 25,
        "parent_hub": "community",
        "capabilities": [
            "xp.rank.view",
            "xp.leaderboard.view",
            "xp.settings.configure",
        ],
    },
    # Karma (thanks/upvote reputation): members grant each other peer
    # reputation; per-user totals + a leaderboard category, on an audited
    # mutation seam (services/karma_service.py).  Config is editable through
    # the !settings widget via the SubsystemSchema in cogs/karma/schemas.py.
    "karma": {
        "display_name": "Karma",
        "description": "Peer reputation — thank helpful members with !thanks",
        "emoji": "✨",
        "color": ROLE_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "progression",
        "tags": ["karma", "reputation", "thanks", "progression", "leaderboard"],
        "entry_points": ["thanks", "karma"],
        "default_channels": ["bot-commands", "general"],
        "related_subsystems": ["xp", "leaderboard"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 26,
        "parent_hub": "community",
        "capabilities": [
            "karma.card.view",
            "karma.grant.give",
            "karma.settings.configure",
        ],
    },
    "role": {
        "display_name": "Roles",
        "description": "Time-based and XP-based automatic role assignment",
        "emoji": "🎭",
        "color": ROLE_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "management",
        "tags": ["roles", "assignment", "automation"],
        "entry_points": ["rolemenu"],
        "default_channels": ["staff", "bot-commands"],
        "related_subsystems": ["xp"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": True,
        "ui_priority": 70,
        "parent_hub": "community",
        "capabilities": [
            "role.settings.configure",
            "role.threshold.configure",
            "role.assignment.manage",
            "role.reaction.manage",
        ],
    },
    "channel": {
        "display_name": "Channels",
        "description": "Channel and category creation, deletion, and restrictions",
        "emoji": "📐",
        "color": CHANNEL_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "management",
        "tags": ["channels", "management", "permissions"],
        "entry_points": ["channelmenu"],
        "default_channels": ["staff"],
        "related_subsystems": [],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": True,
        "ui_priority": 75,
        "parent_hub": "admin",
        "capabilities": [
            "channel.create.text",
            "channel.create.voice",
            "channel.delete.any",
            "channel.restrict.apply",
            "channel.visibility.configure",
        ],
    },
    "cleanup": {
        "display_name": "Cleanup",
        "description": "Prohibited words, command deletion, channel hygiene",
        "emoji": "🧹",
        "color": ADMIN_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "moderation",
        "tags": ["cleanup", "words", "moderation", "hygiene"],
        "entry_points": ["cleanup", "wordmenu", "cleanuphistory"],
        "default_channels": ["staff"],
        "related_subsystems": ["moderation"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 72,
        "parent_hub": "moderation",
        "capabilities": [
            "cleanup.word.add",
            "cleanup.word.remove",
            "cleanup.history.scan",
            "cleanup.policy.configure",
        ],
    },
    # automod v1 (Q-0108) — the automated message-filter layer beneath manual
    # moderation; the twin of ``cleanup`` (auto-mod tier, message-pipeline
    # stage, parented to the moderation hub).  Config is editable through the
    # !settings widget via the SubsystemSchema in cogs/automod/schemas.py.
    "automod": {
        "display_name": "Automod",
        "description": "Spam, invite links, excessive caps, and mass-mention filtering",
        "emoji": "🛡️",
        "color": MOD_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "moderation",
        "tags": ["automod", "moderation", "safety", "spam", "filter"],
        "entry_points": ["automod"],
        "default_channels": ["staff"],
        "related_subsystems": ["moderation", "cleanup"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 73,
        "parent_hub": "moderation",
        "capabilities": [
            "automod.settings.configure",
        ],
    },
    # image moderation v1 (Q-0108) — the automated image-filter layer beneath
    # manual moderation; the image twin of ``automod`` (auto-mod tier,
    # message-pipeline stage, parented to the moderation hub).  Scans uploaded
    # images via OpenAI's free omni-moderation endpoint; config is editable
    # through the !settings widget via cogs/image_moderation/schemas.py.
    "image_moderation": {
        "display_name": "Image moderation",
        "description": "Scan uploaded images for sexual, violent, harassment, or hate content",
        "emoji": "🖼️",
        "color": MOD_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "moderation",
        "tags": ["image", "moderation", "safety", "nsfw", "filter"],
        "entry_points": ["imagemod"],
        "default_channels": ["staff"],
        "related_subsystems": ["moderation", "automod"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 74,
        "parent_hub": "moderation",
        "capabilities": [
            "image_moderation.settings.configure",
        ],
    },
    "games": {
        "display_name": "Games",
        "description": "Competitive games and channel activities",
        "emoji": "🎮",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["games", "hub", "activities"],
        "entry_points": ["games"],
        "default_channels": ["games", "bot-commands"],
        "related_subsystems": [
            "blackjack",
            "rps_tournament",
            "deathmatch",
            "mining",
            "counting",
            "chain",
        ],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 28,
        "capabilities": [
            "games.hub.view",
        ],
    },
    "community": {
        "display_name": "Community",
        "description": "Progression, roles, and community activities",
        "emoji": "🌱",
        "color": GENERAL_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "community",
        "tags": ["community", "hub", "progression"],
        "entry_points": ["community"],
        "default_channels": ["general", "bot-commands"],
        "related_subsystems": ["xp", "role", "counting", "chain", "leaderboard"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 29,
        "capabilities": [
            "community.hub.view",
        ],
    },
    # Key is snake_case (Q-0026): cog_name_to_subsystem("CommunitySpotlightCog")
    # = "community_spotlight".  Registered via the Q-0025 scaffold lane (Q-0044):
    # a read-only live dashboard, reached as a Community-hub child.
    "community_spotlight": {
        "display_name": "Community Spotlight",
        "description": "Live server activity dashboard — leaders, level-ups, game stats",
        "emoji": "🌟",
        "color": GENERAL_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "community",
        "tags": ["spotlight", "activity", "leaderboard", "community"],
        "entry_points": ["spotlight"],
        "default_channels": ["general", "bot-commands"],
        "related_subsystems": ["xp", "economy", "leaderboard"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 30,
        "parent_hub": "community",
        "hub_group": "activities",
        "capabilities": [
            "community_spotlight.dashboard.view",
        ],
    },
    # welcome v1 (owner decision Q-0110): the member-greeting layer of the
    # safety/community platform. Admin-configured (visibility_tier). Homed under
    # the Community hub by the help-menu regrouping (PR #1290); its
    # administrator visibility_tier keeps it hidden from the user-tier Community
    # view and surfaced only to operators, so users still see no operator config.
    "welcome": {
        "display_name": "Welcome",
        "description": "Member greetings, farewells, and an optional entry role",
        "emoji": "👋",
        "color": GENERAL_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "community",
        "tags": ["welcome", "greeting", "onboarding", "community"],
        "entry_points": ["welcome"],
        "default_channels": ["general", "bot-commands"],
        "related_subsystems": ["role", "logging"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 31,
        "parent_hub": "community",
        "capabilities": [
            "welcome.settings.configure",
        ],
    },
    # server counters v1 (owner decision Q-0110): live stat channels (the
    # statdock pattern). Admin-configured. Homed under the Community hub by the
    # help-menu regrouping (PR #1290); its administrator visibility_tier keeps
    # it operator-only in the Community view. Renamed channels are driven by a
    # slow periodic loop (Discord rename rate limit), never per join.
    "counters": {
        "display_name": "Server Counters",
        "description": "Live member-count channels (total · humans · bots)",
        "emoji": "📊",
        "color": GENERAL_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "community",
        "tags": ["counters", "stats", "members", "community"],
        "entry_points": ["counters"],
        "default_channels": ["general"],
        "related_subsystems": ["community_spotlight", "welcome"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 32,
        "parent_hub": "community",
        "capabilities": [
            "counters.settings.configure",
        ],
    },
    # security tiers 1+2 (owner decision Q-0111): the automated join-screening
    # layer (raid detection + account-age filter) beneath manual moderation.
    # Admin-configured. Homed under the Moderation & Safety hub by the help-menu
    # regrouping (PR #1290) — its natural section; its administrator
    # visibility_tier keeps it operator-only. Actions route through
    # moderation_service; the two DECLINED tiers (alt-detection / VPN blocking)
    # are deliberately absent.
    "security": {
        "display_name": "Server Security",
        "description": "Raid detection + account-age screening on member join",
        "emoji": "🛡️",
        "color": GENERAL_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "moderation",
        "tags": ["security", "raid", "moderation", "safety"],
        "entry_points": ["security"],
        "default_channels": ["mod-log", "general"],
        "related_subsystems": ["moderation", "logging", "welcome"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 33,
        "parent_hub": "moderation",
        "capabilities": [
            "security.settings.configure",
        ],
    },
    "blackjack": {
        "display_name": "Blackjack",
        "description": "Blackjack card game",
        "emoji": "🃏",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["games", "blackjack", "cards"],
        "entry_points": ["blackjack", "bj"],
        "default_channels": ["games", "bot-commands"],
        "related_subsystems": ["economy", "deathmatch"],
        "dependencies": [],
        "soft_dependencies": ["economy"],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 30,
        "parent_hub": "games",
        "hub_group": "competitive",
        "capabilities": [
            "blackjack.game.play",
            "blackjack.tournament.manage",
        ],
    },
    "casino": {
        "display_name": "Casino",
        "description": "Group card games like multiplayer poker",
        "emoji": "🎰",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["games", "casino", "poker", "cards", "multiplayer"],
        "entry_points": ["casino", "poker", "holdem"],
        "default_channels": ["games", "bot-commands"],
        "related_subsystems": ["blackjack"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 31,
        "parent_hub": "games",
        "hub_group": "competitive",
        "capabilities": [
            "casino.game.play",
        ],
    },
    "btd6": {
        "display_name": "BTD6 Assistant",
        "description": (
            "Deterministic Bloons Tower Defense 6 assistant — tower/hero/map "
            "lookups, round threat summaries, and CHIMPS-mode guidance. "
            "Built on validated fixtures; consumes the AI gateway only when "
            "explicitly enabled (Module 5)."
        ),
        "emoji": "🐵",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["games", "btd6", "bloons", "tower defense"],
        "entry_points": ["btd6", "btd6menu"],
        "default_channels": ["games", "bot-commands"],
        "related_subsystems": ["ai"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        # M1: BTD6 promoted from Games child to its own top-level Help
        # section. The hub-registry HubEntry is the presentation side;
        # this entry drops parent_hub/hub_group so it no longer appears
        # under Games. ui_priority moves into the top-level band.
        "ui_priority": 32,
        "capabilities": [
            "btd6.query.ask",
            "btd6.strategy.view",
            "btd6.diagnostics.view",
            # M4: strategy submission channel binding capability.
            "btd6.settings.configure",
        ],
    },
    "project_moon": {
        "display_name": "Project Moon",
        "description": (
            "Browsable Limbus Company knowledge — the 12 Sinners, the 7 Sins, "
            "status keywords, damage types, and E.G.O grades. Read-only, "
            "deterministic reference built on committed structural facts."
        ),
        "emoji": "🌑",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["games", "project moon", "limbus", "reference"],
        "entry_points": ["pm", "limbus"],
        "default_channels": ["games", "bot-commands"],
        "related_subsystems": ["ai", "btd6"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": True,
        "has_cleanup_rules": False,
        # Its own top-level Help hub (like BTD6) — a knowledge/reference domain,
        # not a Games activity, so it is deliberately NOT a Games child (that
        # would wrongly subject a read-only browse panel to the Games
        # actionability contract). The hub-registry HubEntry is the
        # presentation side. ui_priority sits in the top-level band near BTD6.
        "ui_priority": 34,
        "capabilities": [
            "project_moon.lookup.view",
        ],
    },
    "deathmatch": {
        "display_name": "Deathmatch",
        "description": "1v1 duel battles",
        "emoji": "⚔️",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["games", "duel", "pvp", "deathmatch"],
        "entry_points": ["deathmatch", "dm"],
        "default_channels": ["games", "bot-commands"],
        "related_subsystems": ["economy", "blackjack"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 32,
        "parent_hub": "games",
        "hub_group": "competitive",
        "capabilities": [
            "deathmatch.game.challenge",
            "deathmatch.stat.view",
        ],
    },
    "rps_tournament": {
        "display_name": "Rock Paper Scissors",
        "description": "Rock Paper Scissors: quick play, PvP, bot matches, tournaments",
        "emoji": "✂️",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["games", "rps", "tournament"],
        "entry_points": ["rps"],
        "default_channels": ["games", "tournament"],
        "related_subsystems": [],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 34,
        "parent_hub": "games",
        "hub_group": "competitive",
        "capabilities": [
            "rps_tournament.game.join",
            "rps_tournament.tournament.manage",
        ],
    },
    "counting": {
        "display_name": "Counting",
        "description": "Collaborative counting game",
        "emoji": "🔢",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["games", "counting", "community"],
        # Player-facing entry points lead (count_info shows live state + top
        # counters; counttop the leaderboard) so counting has a public discovery
        # surface — countingmenu stays for the staff config hub.
        "entry_points": ["count_info", "counttop", "countingmenu"],
        "default_channels": ["counting", "games"],
        "related_subsystems": [],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 36,
        "parent_hub": "games",
        "hub_group": "activities",
        "capabilities": [
            "counting.game.play",
            "counting.game.configure",
        ],
    },
    "chain": {
        "display_name": "Word Chain",
        "description": "Word-chaining game",
        "emoji": "🔗",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["games", "words", "chain"],
        "entry_points": ["chainmenu", "chain"],
        "default_channels": ["games", "bot-commands"],
        "related_subsystems": [],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 38,
        "parent_hub": "games",
        "hub_group": "activities",
        "capabilities": [
            "chain.game.play",
            "chain.game.configure",
        ],
    },
    "leaderboard": {
        "display_name": "Leaderboard",
        "description": "Server leaderboards for XP, coins, and games",
        "emoji": "🏆",
        "color": UTILITY_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "progression",
        "tags": ["leaderboard", "rankings", "stats"],
        "entry_points": ["leaderboard", "lb"],
        "default_channels": ["bot-commands", "general"],
        "related_subsystems": ["xp", "economy"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 40,
        "parent_hub": "economy",
        "capabilities": [
            "leaderboard.xp.view",
            "leaderboard.economy.view",
        ],
    },
    "proof_channel": {
        "display_name": "Proof Channel",
        "description": "Proof submission and exclusive access sessions",
        "emoji": "📋",
        "color": MOD_COLOR.value,
        "visibility_tier": "staff",
        "visibility_mode": "normal",
        "category": "moderation",
        "tags": ["proof", "events", "access"],
        "entry_points": ["prizemenu", "prizestatus", "timedprize"],
        "default_channels": ["staff", "proof"],
        "related_subsystems": ["moderation"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 65,
        "parent_hub": "moderation",
        "capabilities": [
            "proof_channel.access.grant",
            "proof_channel.access.revoke",
            "proof_channel.access.timed",
            "proof_channel.settings.configure",
        ],
    },
    "utility": {
        "display_name": "Utility",
        "description": "General utility commands",
        "emoji": "🔧",
        "color": UTILITY_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "utility",
        "tags": ["utility", "tools", "general"],
        "entry_points": ["utilitymenu", "myprofile", "avatar", "serverinfo", "ping"],
        "default_channels": ["bot-commands", "general"],
        "related_subsystems": ["general"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": True,
        "has_cleanup_rules": False,
        "ui_priority": 5,
        "capabilities": [
            "utility.info.server",
            "utility.info.user",
            "utility.tool.ping",
        ],
    },
    "general": {
        "display_name": "General",
        "description": "General bot commands and information",
        "emoji": "💬",
        "color": GENERAL_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "utility",
        "tags": ["general", "info", "community"],
        "entry_points": ["generalmenu"],
        "default_channels": ["general", "bot-commands"],
        "related_subsystems": ["utility"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 3,
        "parent_hub": "utility",
        "capabilities": [
            "general.info.view",
            "general.community.interact",
        ],
    },
    "four_twenty": {
        "display_name": "420",
        "description": "A leafy little easter-egg panel — wisdom and number trivia",
        "emoji": "🍃",
        "color": GENERAL_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "utility",
        "tags": ["fun", "easter-egg", "420"],
        "entry_points": ["420", "fourtwenty"],
        "default_channels": ["general", "bot-commands"],
        "related_subsystems": ["general"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": True,
        "has_cleanup_rules": False,
        "ui_priority": 4,
        "parent_hub": "utility",
        "capabilities": [
            "four_twenty.panel.view",
        ],
    },
    "help": {
        "display_name": "Help",
        "description": "Interactive help menu and command discovery",
        "emoji": "📚",
        "color": UTILITY_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "utility",
        "tags": ["help", "commands", "discovery"],
        "entry_points": ["help"],
        "default_channels": ["bot-commands", "general"],
        "related_subsystems": [],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": True,
        "has_cleanup_rules": False,
        "ui_priority": 1,
        "capabilities": [
            "help.menu.view",
            "help.settings.configure",
        ],
    },
    "diagnostic": {
        "display_name": "Diagnostics",
        "description": "Bot health, latency, and system diagnostics",
        "emoji": "🩺",
        "color": ADMIN_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "admin",
        "tags": ["diagnostics", "health", "latency", "debug"],
        "entry_points": ["diagnostics", "latency", "platform"],
        "default_channels": ["staff", "bot-spam"],
        "related_subsystems": ["admin"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": True,
        "ui_priority": 95,
        "parent_hub": "admin",
        "capabilities": [
            "diagnostic.health.view",
            "diagnostic.latency.check",
        ],
    },
    "ux_lab": {
        "display_name": "UX Lab",
        "description": "Interface gallery — browse UI patterns, all fake & safe",
        "emoji": "🧪",
        "color": ADMIN_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "admin",
        "tags": ["admin", "design", "gallery", "patterns"],
        "entry_points": ["uxlab"],
        "default_channels": ["staff", "bot-spam"],
        "related_subsystems": [],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 20,
        "parent_hub": "admin",
        # Zero-write workbench: the lab mutates nothing (CI-fenced by
        # tests/unit/invariants/test_ux_lab_zero_write.py), so it holds no
        # capability of its own — authority is the administrator floor on
        # the command plus the view's author lock.
        "capabilities": [],
    },
    "ai": {
        "display_name": "AI Platform",
        "description": (
            "Read-only AI gateway diagnostics: provider state, feature "
            "flags, task routing, and request/failure counters. "
            "Does not own AI provider logic — that lives in "
            "core/runtime/ai/."
        ),
        "emoji": "🤖",
        "color": ADMIN_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "admin",
        "tags": ["ai", "platform", "diagnostics", "providers"],
        "entry_points": ["ai", "aimenu"],
        "default_channels": ["staff", "bot-spam"],
        "related_subsystems": ["diagnostic", "admin"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 88,
        "parent_hub": "admin",
        "capabilities": [
            "ai.platform.view",
            "ai.diagnostics.view",
            "ai.provider.view",
            "ai.routing.view",
            # M1: AI cog hosts the auto-dispatched settings UI for the
            # AI subsystem schema (cogs/ai/schemas.py). These two
            # capabilities gate writes/reads through the existing
            # SettingsMutationPipeline / BindingMutationPipeline lanes.
            "ai.settings.configure",
            "ai.settings.view",
        ],
    },
    "settings": {
        "display_name": "Settings Manager",
        "description": (
            "Read-only browsing of platform settings, bindings, and audit history (S5)"
        ),
        "emoji": "⚙️",
        "color": ADMIN_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "admin",
        "tags": ["settings", "configuration", "audit", "platform"],
        "entry_points": ["settings"],
        "default_channels": ["staff", "bot-admin"],
        "related_subsystems": ["admin", "diagnostic"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 92,
        "parent_hub": "admin",
        "capabilities": [
            "settings.manager.view",
        ],
    },
    "logging": {
        "display_name": "Server Logging",
        "description": (
            "Per-guild moderation/cleanup event logging — channel "
            "selection, auto-create, and audit (S7)"
        ),
        "emoji": "📝",
        "color": ADMIN_COLOR.value,
        "visibility_tier": "administrator",
        "visibility_mode": "normal",
        "category": "admin",
        "tags": ["logging", "audit", "moderation", "cleanup"],
        "entry_points": ["logging"],
        "default_channels": ["staff", "bot-mod-log", "bot-cleanup-log"],
        "related_subsystems": ["moderation", "cleanup", "admin"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 85,
        "parent_hub": "moderation",
        "capabilities": [
            "logging.settings.configure",
            "logging.channel.bind",
            "logging.channel.create",
        ],
    },
}

# ---------------------------------------------------------------------------
# Transitional command → subsystem map.
# Future direction: command.extras["subsystem"] or @subsystem() decorator.
# Do NOT add new features that depend on this dict being comprehensive.
# ---------------------------------------------------------------------------

COMMAND_TO_SUBSYSTEM: dict[str, str] = {
    cmd: name
    for name, meta in SUBSYSTEMS.items()
    for cmd in meta.get("entry_points", [])
}

CAPABILITY_TO_SUBSYSTEM: dict[str, str] = {
    cap: name
    for name, meta in SUBSYSTEMS.items()
    for cap in meta.get("capabilities", [])
}

# ---------------------------------------------------------------------------
# Compiled lookup tables — populated by validate_registry(), O(1) access.
# ---------------------------------------------------------------------------

_COMPILED_DEPENDENTS: dict[str, list[str]] = {}  # subsystem → dependents list
_COMPILED_TIERS: dict[str, str] = {}
_COMPILED_CAPABILITIES: dict[str, list[str]] = {}
_COMPILED_ENTRYPOINTS: dict[str, list[str]] = {}
_COMPILED_DEPENDENCY_ORDER: list[str] = []  # topological order

# ---------------------------------------------------------------------------
# Reserved capability namespaces
# ---------------------------------------------------------------------------

_RESERVED_CAPABILITY_PREFIXES: frozenset[str] = frozenset(
    {"_internal", "system", "governance"},
)


def is_reserved_capability(cap: str) -> bool:
    return cap.split(".")[0] in _RESERVED_CAPABILITY_PREFIXES


# ---------------------------------------------------------------------------
# Capability dataclass — centralises parsing, eliminates repeated .split(".")
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Capability:
    """Immutable representation of a capability string.

    Format: {subsystem}.{resource}.{action}
    Raises CapabilityNamespaceError if the format is invalid.
    """

    subsystem: str
    resource: str
    action: str

    @classmethod
    def parse(cls, raw: str) -> Capability:
        from services.governance_exceptions import CapabilityNamespaceError

        parts = raw.split(".")
        if len(parts) != 3:
            raise CapabilityNamespaceError(
                f"'{raw}' must be {{subsystem}}.{{resource}}.{{action}}",
            )
        return cls(*parts)

    def __str__(self) -> str:
        return f"{self.subsystem}.{self.resource}.{self.action}"

    def matches_pattern(self, pattern: str) -> bool:
        return capability_matches(pattern, str(self))


# ---------------------------------------------------------------------------
# Deep freeze helper
# ---------------------------------------------------------------------------


def _deep_freeze(obj):
    """Recursively convert dicts→MappingProxyType, lists→tuple, sets→frozenset."""
    if isinstance(obj, dict):
        return MappingProxyType({k: _deep_freeze(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return tuple(_deep_freeze(v) for v in obj)
    if isinstance(obj, set):
        return frozenset(_deep_freeze(v) for v in obj)
    return obj


# ---------------------------------------------------------------------------
# Registry validation + compilation
# ---------------------------------------------------------------------------


def validate_registry() -> None:
    """Run once at bot startup. Populates compiled tables and deep-freezes registry.

    Raises:
        RegistryValidationError subclasses on any integrity violation.
    """
    from services.governance_exceptions import (
        CapabilityNamespaceError,
        CircularDependencyError,
        RegistryValidationError,
    )

    global _COMPILED_DEPENDENTS, _COMPILED_TIERS, _COMPILED_CAPABILITIES
    global _COMPILED_ENTRYPOINTS

    seen_caps: set[str] = set()
    seen_entries: set[str] = set()
    valid_tiers = {"user", "trusted", "staff", "moderator", "administrator", "owner"}
    valid_modes = {"normal", "hidden", "internal", "deprecated", "experimental"}
    all_names = set(SUBSYSTEMS)
    dep_graph: dict[str, list[str]] = {}

    for name, meta in SUBSYSTEMS.items():
        for field in (
            "display_name",
            "description",
            "emoji",
            "visibility_tier",
            "visibility_mode",
        ):
            if not meta.get(field):
                raise RegistryValidationError(
                    f"subsystem '{name}': missing required field '{field}'",
                )
        if meta["visibility_tier"] not in valid_tiers:
            raise RegistryValidationError(
                f"subsystem '{name}': invalid visibility_tier '{meta['visibility_tier']}'",
            )
        if meta["visibility_mode"] not in valid_modes:
            raise RegistryValidationError(
                f"subsystem '{name}': invalid visibility_mode '{meta['visibility_mode']}'",
            )
        if not isinstance(meta.get("color", 0), int):
            raise RegistryValidationError(
                f"subsystem '{name}': color must be int (.value), not discord.Color",
            )

        for cap in meta.get("capabilities", []):
            if is_reserved_capability(cap):
                raise CapabilityNamespaceError(
                    f"subsystem '{name}': capability '{cap}' uses reserved namespace",
                )
            if len(cap.split(".")) != 3:
                raise CapabilityNamespaceError(
                    f"subsystem '{name}': capability '{cap}' must be"
                    " {subsystem}.{resource}.{action}",
                )
            if cap in seen_caps:
                raise RegistryValidationError(f"Duplicate capability: '{cap}'")
            seen_caps.add(cap)

        for ep in meta.get("entry_points", []):
            if ep in seen_entries:
                raise RegistryValidationError(f"Duplicate entry_point: '{ep}'")
            seen_entries.add(ep)

        for dep in meta.get("dependencies", []):
            if dep not in all_names:
                raise RegistryValidationError(
                    f"subsystem '{name}': unknown dependency '{dep}'",
                )
        for rel in meta.get("related_subsystems", []):
            if rel not in all_names:
                raise RegistryValidationError(
                    f"subsystem '{name}': unknown related_subsystem '{rel}'",
                )

        # parent_hub / hub_group — optional Phase 1 metadata (schema v2)
        parent_hub = meta.get("parent_hub")
        if parent_hub is not None:
            if not isinstance(parent_hub, str) or not parent_hub:
                raise RegistryValidationError(
                    f"subsystem '{name}': parent_hub must be a non-empty string",
                )
            if parent_hub == name:
                raise RegistryValidationError(
                    f"subsystem '{name}': parent_hub cannot reference self",
                )
            if parent_hub not in all_names:
                raise RegistryValidationError(
                    f"subsystem '{name}': parent_hub '{parent_hub}' is not a "
                    f"registered subsystem",
                )

        hub_group = meta.get("hub_group")
        if hub_group is not None:
            if not isinstance(hub_group, str) or not hub_group:
                raise RegistryValidationError(
                    f"subsystem '{name}': hub_group must be a non-empty string",
                )
            if len(hub_group) > _HUB_GROUP_MAX_LEN:
                raise RegistryValidationError(
                    f"subsystem '{name}': hub_group length must be ≤ "
                    f"{_HUB_GROUP_MAX_LEN} (got {len(hub_group)})",
                )

        dep_graph[name] = list(meta.get("dependencies", []))

    # parent_hub cross-entry checks: no two-hop hubs, hub must be routable.
    # A second pass is needed because each entry's parent_hub references
    # another entry and the referenced entry's own parent_hub must be
    # known to validate the no-two-hop rule.
    for name, meta in SUBSYSTEMS.items():
        parent_hub = meta.get("parent_hub")
        if parent_hub is None:
            continue
        parent_meta = SUBSYSTEMS[parent_hub]
        if parent_meta.get("parent_hub") is not None:
            raise RegistryValidationError(
                f"subsystem '{name}': parent_hub '{parent_hub}' itself has a "
                f"parent_hub — two-hop hubs are not allowed",
            )
        if not parent_meta.get("entry_points"):
            raise RegistryValidationError(
                f"subsystem '{name}': parent_hub '{parent_hub}' has no "
                f"entry_points and is not routable",
            )

    # DFS cycle detection
    visited: set[str] = set()
    rec_stack: set[str] = set()

    def _dfs(node: str) -> None:
        visited.add(node)
        rec_stack.add(node)
        for neighbour in dep_graph.get(node, []):
            if neighbour not in visited:
                _dfs(neighbour)
            elif neighbour in rec_stack:
                raise CircularDependencyError(node, neighbour)
        rec_stack.discard(node)

    for name in SUBSYSTEMS:
        if name not in visited:
            _dfs(name)

    # Topological sort — deps appear before their dependents
    topo_order: list[str] = []
    topo_visited: set[str] = set()

    def _topo(node: str) -> None:
        if node in topo_visited:
            return
        topo_visited.add(node)
        for dep in dep_graph.get(node, []):
            _topo(dep)
        topo_order.append(node)

    for name in SUBSYSTEMS:
        _topo(name)

    # Populate compiled lookup tables
    compiled_tiers = {
        name: meta["visibility_tier"] for name, meta in SUBSYSTEMS.items()
    }
    compiled_caps = {
        name: meta.get("capabilities", []) for name, meta in SUBSYSTEMS.items()
    }
    compiled_eps = {
        name: meta.get("entry_points", []) for name, meta in SUBSYSTEMS.items()
    }
    compiled_dependents: dict[str, list[str]] = {name: [] for name in SUBSYSTEMS}
    for name, deps in dep_graph.items():
        for dep in deps:
            compiled_dependents[dep].append(name)

    _COMPILED_DEPENDENCY_ORDER[:] = topo_order
    _COMPILED_TIERS.update(compiled_tiers)
    _COMPILED_CAPABILITIES.update(compiled_caps)
    _COMPILED_ENTRYPOINTS.update(compiled_eps)
    _COMPILED_DEPENDENTS.update(compiled_dependents)

    # Deep-freeze — after this point any mutation attempt raises TypeError
    globals()["SUBSYSTEMS"] = _deep_freeze(SUBSYSTEMS)
    globals()["COMMAND_TO_SUBSYSTEM"] = MappingProxyType(COMMAND_TO_SUBSYSTEM)
    globals()["CAPABILITY_TO_SUBSYSTEM"] = MappingProxyType(CAPABILITY_TO_SUBSYSTEM)
    globals()["_COMPILED_DEPENDENTS"] = _deep_freeze(compiled_dependents)
    globals()["_COMPILED_TIERS"] = MappingProxyType(compiled_tiers)
    globals()["_COMPILED_CAPABILITIES"] = _deep_freeze(compiled_caps)
    globals()["_COMPILED_ENTRYPOINTS"] = _deep_freeze(compiled_eps)


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------


def get_subsystem(name: str) -> dict | None:
    return SUBSYSTEMS.get(name)  # type: ignore[return-value]


def get_subsystem_for_command(command_name: str) -> tuple[str, dict] | None:
    name = COMMAND_TO_SUBSYSTEM.get(command_name)
    if name and name in SUBSYSTEMS:
        return name, SUBSYSTEMS[name]  # type: ignore[return-value]
    return None


def get_subsystem_for_capability(capability: str) -> tuple[str, dict] | None:
    name = CAPABILITY_TO_SUBSYSTEM.get(capability)
    if name and name in SUBSYSTEMS:
        return name, SUBSYSTEMS[name]  # type: ignore[return-value]
    return None


def all_subsystems_sorted() -> list[tuple[str, dict]]:
    """All subsystems sorted by ui_priority (ascending)."""
    return sorted(
        SUBSYSTEMS.items(),  # type: ignore[arg-type]
        key=lambda x: x[1].get("ui_priority", 99),
    )


# ---------------------------------------------------------------------------
# Identity-contract findings — tier classification (PR I1a).
#
# ``validate_identity_contract`` returns findings grouped by *kind*; this
# table maps each kind to a severity tier.  The startup orchestrator
# (bot1.py) consumes the tiers to decide whether to log, emit a metric,
# or (in a later PR I1b) abort startup / self-heal.
#
# Tier semantics:
#   fatal          — violates routing or help/navigation integrity.  In
#                    I1a these still WARN (no abort); STRICT enforcement
#                    is deferred to I1b.  Listed here so future code can
#                    gate on the classification without changing it.
#   auto_healable  — safe for an admin (or, in I1b, an automated job) to
#                    remediate without operator intervention: orphan
#                    router prefixes can be unregistered, orphan view
#                    classes can be skipped, orphan anchor rows can be
#                    marked stale.
#   warn_only      — informational; surfaced but not actionable as a
#                    finding in isolation (none currently classified).
#
# Invariant: ``set(IDENTITY_FINDING_TIER) == set(findings)`` after every
# validator run.  The regression test enforces this — a new finding
# bucket added without a tier classification will fail CI.
# ---------------------------------------------------------------------------
IDENTITY_FINDING_TIER: dict[str, str] = {
    "entry_point_missing_command": "fatal",
    "router_prefix_unknown": "auto_healable",
    "view_subsystem_unknown": "auto_healable",
    "db_anchor_subsystem_unknown": "auto_healable",
    # Phase 1 schema findings — warn_only initially.  Phase 6 promotes
    # ``schema_subsystem_unknown`` to ``auto_healable`` once orphan
    # schemas are reliably detectable + safely unregisterable.  The
    # capability-drift kind stays warn_only — fixing it requires
    # editing SUBSYSTEMS, not the schema registry.
    "schema_subsystem_unknown": "warn_only",
    "participation_schema_subsystem_unknown": "warn_only",
    "schema_capability_unknown": "warn_only",
}


def summarize_findings(findings: dict[str, list[str]]) -> dict[str, object]:
    """Compute a tiered summary of identity-contract findings.

    Returns a dict with three keys:
      * ``total`` (int): total findings across all kinds.
      * ``by_kind`` (dict[str, int]): per-bucket counts.
      * ``by_tier`` (dict[str, int]): counts grouped by severity tier
        (``fatal`` / ``auto_healable`` / ``warn_only``).  Tiers with
        zero findings are still included so the schema is stable.

    The validator's return shape is unchanged; this is a sibling helper
    consumed by the startup orchestrator and the ``!platform identity``
    admin command.
    """
    by_kind: dict[str, int] = {kind: len(items) for kind, items in findings.items()}
    by_tier: dict[str, int] = {"fatal": 0, "auto_healable": 0, "warn_only": 0}
    for kind, count in by_kind.items():
        tier = IDENTITY_FINDING_TIER.get(kind)
        if tier is None:
            # Unknown kind — defensively count under fatal so the
            # invariant test catches the missing classification.
            tier = "fatal"
        by_tier[tier] += count
    return {
        "total": sum(by_kind.values()),
        "by_kind": by_kind,
        "by_tier": by_tier,
    }


async def validate_identity_contract(bot: object) -> dict[str, list[str]]:
    """Cross-check that the four subsystem-identity surfaces agree.

    Runs after cogs load.  The four surfaces that MUST all use the same
    subsystem-name strings are:

      1. ``SUBSYSTEMS`` keys (this module's manifest)
      2. ``commands.Cog`` command names registered on the bot
      3. ``core.runtime.persistent_views._REGISTRY`` keys (the
         ``SUBSYSTEM`` class-var of every ``PersistentView`` subclass)
      4. ``core.runtime.interaction_router._handlers`` prefixes
      5. distinct ``panel_anchors.subsystem`` values from the DB

    A mismatch in any of these silently breaks: help menus show
    categories whose commands don't exist; ``restore_anchors`` skips
    panels; the interaction router drops button clicks; old anchor rows
    point at removed cogs.

    The validator logs a WARNING per finding and returns the structured
    report so callers (admin commands, tests) can inspect it.  It does
    NOT raise on findings — a mismatched DB row from a removed cog
    should never abort startup.

    Implements INV-B from the platform-hardening plan.

    Args:
        bot: a ``commands.Bot`` instance.  Typed as ``object`` here so
            this module needn't import discord at validation time.

    Returns:
        Dict with keys ``entry_point_missing_command``,
        ``router_prefix_unknown``, ``view_subsystem_unknown``,
        ``db_anchor_subsystem_unknown``.  Values are lists of
        descriptive strings (one per finding).
    """
    import logging

    logger = logging.getLogger("bot.identity_contract")

    findings: dict[str, list[str]] = {
        "entry_point_missing_command": [],
        "router_prefix_unknown": [],
        "view_subsystem_unknown": [],
        "db_anchor_subsystem_unknown": [],
        "schema_subsystem_unknown": [],
        "participation_schema_subsystem_unknown": [],
        "schema_capability_unknown": [],
    }

    # Surface 2: bot commands — include aliases so registry entries
    # that reference an alias (e.g. "bj" for blackjack, "deathmatch" for
    # dm_challenge) match without triggering a false drift finding.
    loaded_commands: set[str] = set()
    for cmd in getattr(bot, "commands", ()):
        loaded_commands.add(cmd.name)
        loaded_commands.update(cmd.aliases)

    # Surface 1 vs Surface 2.
    for sub_name, meta in SUBSYSTEMS.items():
        if meta.get("visibility_mode") == "internal":
            continue
        eps = meta.get("entry_points", ())
        for ep in eps:
            if ep not in loaded_commands:
                msg = f"subsystem={sub_name!r} entry_point={ep!r}"
                findings["entry_point_missing_command"].append(msg)
                logger.warning(
                    "Identity-contract: entry_point %r declared by subsystem "
                    "%r is not a loaded command (cog may have failed to load).",
                    ep,
                    sub_name,
                )

    # Surface 4: interaction_router prefixes.
    try:
        from core.runtime.interaction_router import _handlers as _router_handlers
    except Exception:
        _router_handlers = {}
    for prefix in _router_handlers:
        if prefix not in SUBSYSTEMS:
            findings["router_prefix_unknown"].append(prefix)
            logger.warning(
                "Identity-contract: interaction_router prefix %r has no "
                "matching SUBSYSTEMS entry.",
                prefix,
            )

    # Surface 3: PersistentView SUBSYSTEM class vars.
    try:
        from core.runtime.persistent_views import _REGISTRY as _VIEW_REGISTRY
    except Exception:
        _VIEW_REGISTRY = {}
    for sub_name in _VIEW_REGISTRY:
        if sub_name not in SUBSYSTEMS:
            findings["view_subsystem_unknown"].append(sub_name)
            logger.warning(
                "Identity-contract: PersistentView SUBSYSTEM=%r has no "
                "matching SUBSYSTEMS entry.",
                sub_name,
            )

    # Surface 5: distinct panel_anchors.subsystem values from the DB.
    try:
        from utils import db as _db

        rows = await _db.fetchall(
            "SELECT DISTINCT subsystem FROM panel_anchors WHERE NOT is_stale",
            (),
        )
        for row in rows or ():
            sub_name = row["subsystem"] if isinstance(row, dict) else row[0]
            if sub_name not in SUBSYSTEMS:
                findings["db_anchor_subsystem_unknown"].append(sub_name)
                logger.warning(
                    "Identity-contract: panel_anchors row references "
                    "subsystem %r which has no matching SUBSYSTEMS entry "
                    "(likely orphaned from a removed cog).",
                    sub_name,
                )
    except Exception as exc:
        # DB unavailable at startup, or table not migrated yet — not fatal.
        logger.debug(
            "Identity-contract: skipping panel_anchors check (%s)",
            exc,
        )

    # Phase 1 schema cross-checks (warn_only).  Promoted to enforced in Phase 6.
    try:
        from core.runtime.subsystem_schema import all_schemas as _all_config_schemas

        all_caps: set[str] = set()
        for meta in SUBSYSTEMS.values():
            all_caps.update(meta.get("capabilities", ()))

        for sub_name, schema in _all_config_schemas().items():
            if sub_name not in SUBSYSTEMS:
                findings["schema_subsystem_unknown"].append(sub_name)
                logger.warning(
                    "Identity-contract: SubsystemSchema for %r has no "
                    "matching SUBSYSTEMS entry.",
                    sub_name,
                )
                continue
            for binding in schema.bindings:
                cap = binding.capability_required
                if cap and cap not in all_caps:
                    msg = f"{sub_name}/{binding.name}: capability={cap!r}"
                    findings["schema_capability_unknown"].append(msg)
                    logger.warning(
                        "Identity-contract: SubsystemSchema %r binding %r "
                        "requires capability %r which is not declared in "
                        "any subsystem's capabilities list.",
                        sub_name,
                        binding.name,
                        cap,
                    )
            for setting in schema.settings:
                cap = setting.capability_required
                if cap and cap not in all_caps:
                    msg = f"{sub_name}/{setting.name}: capability={cap!r}"
                    findings["schema_capability_unknown"].append(msg)
                    logger.warning(
                        "Identity-contract: SubsystemSchema %r setting %r "
                        "requires capability %r which is not declared in "
                        "any subsystem's capabilities list.",
                        sub_name,
                        setting.name,
                        cap,
                    )
    except Exception as exc:
        logger.debug("Identity-contract: skipping schema check (%s)", exc)

    try:
        from core.runtime.participation_schema import (
            all_schemas as _all_participation_schemas,
        )

        for sub_name in _all_participation_schemas():
            if sub_name not in SUBSYSTEMS:
                findings["participation_schema_subsystem_unknown"].append(sub_name)
                logger.warning(
                    "Identity-contract: ParticipationSchema for %r has "
                    "no matching SUBSYSTEMS entry.",
                    sub_name,
                )
    except Exception as exc:
        logger.debug(
            "Identity-contract: skipping participation schema check (%s)",
            exc,
        )

    # No trailing summary log here — the startup orchestrator in
    # ``bot1.py`` owns summary logging so the validator and orchestrator
    # do not both emit duplicate WARNING lines.  Per-finding WARNINGs
    # above retain the diagnostic detail that operators need; callers
    # interested in a tiered summary should pass ``findings`` to
    # :func:`summarize_findings`.
    return findings


async def apply_self_heal(findings: dict[str, list[str]]) -> dict[str, int]:
    """Remediate ``auto_healable`` identity-contract findings.

    This helper is *opt-in*; the startup orchestrator never invokes it
    unattended in PR I1b.  It is called manually via
    ``!platform identity --fix`` so an operator can review the validator
    output before consenting to destructive cleanup.

    Actions taken (only for buckets tier-classified ``auto_healable``):

    * ``router_prefix_unknown`` — the orphan handler is popped from
      ``core.runtime.interaction_router._handlers``.  Subsequent
      interactions for that prefix fall through to the
      ``interaction_unhandled_total`` metric path instead of running an
      unauthorised handler.
    * ``view_subsystem_unknown`` — the orphan PersistentView class is
      removed from ``core.runtime.persistent_views._REGISTRY`` so the
      next anchor-restore pass treats it as missing.
    * ``db_anchor_subsystem_unknown`` — every active anchor row whose
      subsystem string is orphaned is bulk-marked stale; the session_gc
      loop deletes stale rows on its next sweep.

    ``fatal``-tier findings (``entry_point_missing_command``) are NEVER
    auto-healed: a missing entry-point command means a cog failed to
    load, and silently "fixing" the registry would mask that.

    Returns a counts dict so callers can render an operator-friendly
    summary:
        {"router_prefixes_unregistered": int,
         "views_unregistered": int,
         "anchors_marked_stale": int,
         "skipped_fatal": int}
    """
    import logging

    logger = logging.getLogger("bot.identity_contract")

    counts = {
        "router_prefixes_unregistered": 0,
        "views_unregistered": 0,
        "anchors_marked_stale": 0,
        "skipped_fatal": 0,
    }

    # router_prefix_unknown → unregister
    if findings.get("router_prefix_unknown"):
        try:
            from core.runtime.interaction_router import _handlers as _router_handlers

            for prefix in findings["router_prefix_unknown"]:
                if _router_handlers.pop(prefix, None) is not None:
                    counts["router_prefixes_unregistered"] += 1
                    logger.info(
                        "Identity-contract self-heal: unregistered orphan "
                        "router prefix %r",
                        prefix,
                    )
        except Exception as exc:
            logger.warning(
                "Identity-contract self-heal: router unregister skipped (%s)",
                exc,
            )

    # view_subsystem_unknown → unregister
    if findings.get("view_subsystem_unknown"):
        try:
            from core.runtime.persistent_views import _REGISTRY as _VIEW_REGISTRY

            for sub_name in findings["view_subsystem_unknown"]:
                if _VIEW_REGISTRY.pop(sub_name, None) is not None:
                    counts["views_unregistered"] += 1
                    logger.info(
                        "Identity-contract self-heal: unregistered orphan "
                        "PersistentView for subsystem %r",
                        sub_name,
                    )
        except Exception as exc:
            logger.warning(
                "Identity-contract self-heal: view unregister skipped (%s)",
                exc,
            )

    # db_anchor_subsystem_unknown → mark stale
    if findings.get("db_anchor_subsystem_unknown"):
        try:
            from utils import db as _db

            for sub_name in findings["db_anchor_subsystem_unknown"]:
                rows = await _db.mark_anchors_stale_for_subsystem(sub_name)
                counts["anchors_marked_stale"] += rows
                logger.info(
                    "Identity-contract self-heal: marked %d anchor row(s) "
                    "stale for orphan subsystem %r",
                    rows,
                    sub_name,
                )
        except Exception as exc:
            logger.warning(
                "Identity-contract self-heal: anchor cleanup skipped (%s)",
                exc,
            )

    # fatal-tier findings are recorded but never auto-healed
    counts["skipped_fatal"] = len(findings.get("entry_point_missing_command", []))
    if counts["skipped_fatal"]:
        logger.warning(
            "Identity-contract self-heal: skipped %d fatal-tier finding(s) "
            "(entry_point_missing_command — requires operator review, likely "
            "a cog failed to load).",
            counts["skipped_fatal"],
        )

    return counts


def capability_matches(pattern: str, capability: str) -> bool:
    """Wildcard capability matching for future declarative policy rules.

    Patterns: 'economy.*.*', 'moderation.message.*', '*.shop.buy'
    Both pattern and capability must have exactly 3 dot-separated parts.
    """
    p_parts = pattern.split(".")
    c_parts = capability.split(".")
    if len(p_parts) != len(c_parts) or len(p_parts) != 3:
        return False
    return all(p == "*" or p == c for p, c in zip(p_parts, c_parts, strict=True))
