"""Subsystem registry — immutable platform metadata manifest.

This file is the single source of truth for all subsystem definitions.
After validate_registry() runs at startup, every structure here is deep-frozen.
Overrides (visibility, cleanup rules) belong in governance DB, never here.

Capability namespace rule: {subsystem}.{resource}.{action} — three parts, enforced.
Reserved prefixes: _internal.*, system.*, governance.*

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
REGISTRY_SCHEMA_VERSION = 1

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
        "visibility_tier": "owner",
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
        "has_onboarding": False,
        "ui_priority": 90,
        "capabilities": [
            "admin.cog.load",
            "admin.cog.unload",
            "admin.cog.reload",
            "admin.server.stats",
        ],
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
        "has_onboarding": False,
        "ui_priority": 80,
        "capabilities": [
            "moderation.warn.apply",
            "moderation.timeout.apply",
            "moderation.kick.apply",
            "moderation.ban.apply",
            "moderation.ban.remove",
            "moderation.log.view",
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
        "has_onboarding": True,
        "ui_priority": 10,
        "capabilities": [
            "economy.currency.view",
            "economy.currency.earn",
            "economy.shop.browse",
            "economy.shop.buy",
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
        "entry_points": ["inventorymenu", "inventory", "craft"],
        "default_channels": ["economy", "bot-commands"],
        "related_subsystems": ["economy", "mining"],
        "dependencies": ["economy"],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "has_onboarding": False,
        "ui_priority": 15,
        "capabilities": [
            "inventory.item.view",
            "inventory.item.use",
            "inventory.craft.recipe",
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
        "entry_points": ["miningmenu", "mine"],
        "default_channels": ["mining", "bot-commands"],
        "related_subsystems": ["economy", "inventory"],
        "dependencies": ["economy"],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "has_onboarding": False,
        "ui_priority": 20,
        "capabilities": [
            "mining.resource.mine",
            "mining.resource.view",
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
        "entry_points": ["xpmenu", "rank", "level"],
        "default_channels": ["bot-commands", "general"],
        "related_subsystems": ["role", "leaderboard"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "has_onboarding": True,
        "ui_priority": 25,
        "capabilities": [
            "xp.rank.view",
            "xp.leaderboard.view",
            "xp.settings.configure",
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
        "has_onboarding": False,
        "ui_priority": 70,
        "capabilities": [
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
        "has_onboarding": False,
        "ui_priority": 75,
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
        "entry_points": ["wordmenu", "cleanuphistory"],
        "default_channels": ["staff"],
        "related_subsystems": ["moderation"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "has_onboarding": False,
        "ui_priority": 72,
        "capabilities": [
            "cleanup.word.add",
            "cleanup.word.remove",
            "cleanup.history.scan",
            "cleanup.policy.configure",
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
        "has_onboarding": False,
        "ui_priority": 30,
        "capabilities": [
            "blackjack.game.play",
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
        "has_onboarding": False,
        "ui_priority": 32,
        "capabilities": [
            "deathmatch.game.challenge",
            "deathmatch.stat.view",
        ],
    },
    "rps_tournament": {
        "display_name": "RPS Tournament",
        "description": "Rock-Paper-Scissors tournament system",
        "emoji": "✂️",
        "color": GAME_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "games",
        "tags": ["games", "rps", "tournament"],
        "entry_points": ["rpsmenu", "rps"],
        "default_channels": ["games", "tournament"],
        "related_subsystems": [],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "has_onboarding": False,
        "ui_priority": 34,
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
        "entry_points": ["countingmenu", "counting"],
        "default_channels": ["counting", "games"],
        "related_subsystems": [],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "has_onboarding": False,
        "ui_priority": 36,
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
        "has_onboarding": False,
        "ui_priority": 38,
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
        "has_onboarding": False,
        "ui_priority": 40,
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
        "has_onboarding": False,
        "ui_priority": 65,
        "capabilities": [
            "proof_channel.access.grant",
            "proof_channel.access.revoke",
            "proof_channel.access.timed",
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
        "entry_points": ["utilitymenu", "avatar", "serverinfo"],
        "default_channels": ["bot-commands", "general"],
        "related_subsystems": ["general"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": True,
        "has_cleanup_rules": False,
        "has_onboarding": False,
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
        "has_onboarding": False,
        "ui_priority": 3,
        "capabilities": [
            "general.info.view",
            "general.community.interact",
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
        "has_onboarding": True,
        "ui_priority": 1,
        "capabilities": [
            "help.menu.view",
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
        "entry_points": ["diagnosticmenu", "diagnostics", "ping"],
        "default_channels": ["staff", "bot-spam"],
        "related_subsystems": ["admin"],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": True,
        "has_onboarding": False,
        "ui_priority": 95,
        "capabilities": [
            "diagnostic.health.view",
            "diagnostic.latency.check",
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
    {"_internal", "system", "governance"}
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
    def parse(cls, raw: str) -> "Capability":
        from services.governance_exceptions import CapabilityNamespaceError

        parts = raw.split(".")
        if len(parts) != 3:
            raise CapabilityNamespaceError(
                f"'{raw}' must be {{subsystem}}.{{resource}}.{{action}}"
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
                    f"subsystem '{name}': missing required field '{field}'"
                )
        if meta["visibility_tier"] not in valid_tiers:
            raise RegistryValidationError(
                f"subsystem '{name}': invalid visibility_tier '{meta['visibility_tier']}'"
            )
        if meta["visibility_mode"] not in valid_modes:
            raise RegistryValidationError(
                f"subsystem '{name}': invalid visibility_mode '{meta['visibility_mode']}'"
            )
        if not isinstance(meta.get("color", 0), int):
            raise RegistryValidationError(
                f"subsystem '{name}': color must be int (.value), not discord.Color"
            )

        for cap in meta.get("capabilities", []):
            if is_reserved_capability(cap):
                raise CapabilityNamespaceError(
                    f"subsystem '{name}': capability '{cap}' uses reserved namespace"
                )
            if len(cap.split(".")) != 3:
                raise CapabilityNamespaceError(
                    f"subsystem '{name}': capability '{cap}' must be"
                    " {subsystem}.{resource}.{action}"
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
                    f"subsystem '{name}': unknown dependency '{dep}'"
                )
        for rel in meta.get("related_subsystems", []):
            if rel not in all_names:
                raise RegistryValidationError(
                    f"subsystem '{name}': unknown related_subsystem '{rel}'"
                )

        dep_graph[name] = list(meta.get("dependencies", []))

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


def capability_matches(pattern: str, capability: str) -> bool:
    """Wildcard capability matching for future declarative policy rules.

    Patterns: 'economy.*.*', 'moderation.message.*', '*.shop.buy'
    Both pattern and capability must have exactly 3 dot-separated parts.
    """
    p_parts = pattern.split(".")
    c_parts = capability.split(".")
    if len(p_parts) != len(c_parts) or len(p_parts) != 3:
        return False
    return all(p == "*" or p == c for p, c in zip(p_parts, c_parts))
