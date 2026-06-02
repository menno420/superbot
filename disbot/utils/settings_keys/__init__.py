"""Guild settings key constants — prevents typo drift and documents ownership.

Each key is owned by exactly one subsystem. Submodules group keys by their
owning subsystem; this ``__init__`` re-exports the full surface so existing
``from utils.settings_keys import NAME`` and ``from utils import settings_keys``
+ ``settings_keys.NAME`` access patterns both keep working.

All ``db.get_setting() / db.set_setting()`` calls must reference these
constants, never raw string literals.

Phase 0 of the platform roadmap introduced the per-subsystem layout; future
additions should land in the appropriate submodule rather than directly in
this ``__init__``.
"""

from utils.settings_keys.ai import (
    AI_COOLDOWN_SECONDS,
    AI_DEFAULT_MODEL,
    AI_DEFAULT_PROVIDER,
    AI_ENABLED,
    AI_FRESH_USER_MENTION_ALLOWANCE,
    AI_GUILD_INSTRUCTION_PROFILE,
    AI_MEMORY_CHANNEL_SCAN_ENABLED,
    AI_MEMORY_WINDOW_MINUTES,
    AI_MINIMUM_LEVEL_DEFAULT,
    AI_NATURAL_LANGUAGE_ENABLED,
)
from utils.settings_keys.btd6 import (
    BTD6_CT_GROUP_ID,
    BTD6_STRATEGY_SUBMISSION_CHANNEL,
)
from utils.settings_keys.btd6_cache import (
    BTD6_CACHE_CIRCUIT_BREAKER_THRESHOLD,
    BTD6_CACHE_DEFAULT_INTERVAL_SECONDS,
    BTD6_CACHE_FRESHNESS_WARNING_HOURS,
)
from utils.settings_keys.economy import ECONOMY_LOG_CHANNEL
from utils.settings_keys.games import (
    ACTIVE_TOURNAMENT,
    BLACKJACK_DEFAULT_ENTRY_FEE,
    DEATHMATCH_TURN_TIMEOUT,
    RPS_DEFAULT_ENTRY_FEE,
)
from utils.settings_keys.governance import GOVERNANCE_VERSION, TRUSTED_TIER_ROLE_ID
from utils.settings_keys.logging import (
    DEFAULT_CLEANUP_CHANNEL_NAME,
    DEFAULT_MOD_CHANNEL_NAME,
    LOGGING_AUTO_CREATE_CHANNELS,
    LOGGING_CLEANUP_CHANNEL,
    LOGGING_ENABLED,
    LOGGING_MOD_CHANNEL,
)
from utils.settings_keys.moderation import WARN_THRESHOLD, WARN_TIMEOUT_MINS
from utils.settings_keys.role import SKIP_ROLES, TIME_ROLES_STACK, XP_ROLES_STACK
from utils.settings_keys.xp import (
    XP_ANNOUNCE_CHANNEL,
    XP_COOLDOWN,
    XP_MAX,
    XP_MIN,
)

__all__ = [
    "ACTIVE_TOURNAMENT",
    "AI_COOLDOWN_SECONDS",
    "AI_DEFAULT_MODEL",
    "AI_DEFAULT_PROVIDER",
    "AI_ENABLED",
    "AI_FRESH_USER_MENTION_ALLOWANCE",
    "AI_GUILD_INSTRUCTION_PROFILE",
    "AI_MEMORY_CHANNEL_SCAN_ENABLED",
    "AI_MEMORY_WINDOW_MINUTES",
    "AI_MINIMUM_LEVEL_DEFAULT",
    "AI_NATURAL_LANGUAGE_ENABLED",
    "BLACKJACK_DEFAULT_ENTRY_FEE",
    "BTD6_CACHE_CIRCUIT_BREAKER_THRESHOLD",
    "BTD6_CACHE_DEFAULT_INTERVAL_SECONDS",
    "BTD6_CACHE_FRESHNESS_WARNING_HOURS",
    "BTD6_CT_GROUP_ID",
    "BTD6_STRATEGY_SUBMISSION_CHANNEL",
    "DEATHMATCH_TURN_TIMEOUT",
    "DEFAULT_CLEANUP_CHANNEL_NAME",
    "DEFAULT_MOD_CHANNEL_NAME",
    "ECONOMY_LOG_CHANNEL",
    "GOVERNANCE_VERSION",
    "LOGGING_AUTO_CREATE_CHANNELS",
    "LOGGING_CLEANUP_CHANNEL",
    "LOGGING_ENABLED",
    "LOGGING_MOD_CHANNEL",
    "RPS_DEFAULT_ENTRY_FEE",
    "SKIP_ROLES",
    "TIME_ROLES_STACK",
    "XP_ROLES_STACK",
    "TRUSTED_TIER_ROLE_ID",
    "WARN_THRESHOLD",
    "WARN_TIMEOUT_MINS",
    "XP_ANNOUNCE_CHANNEL",
    "XP_COOLDOWN",
    "XP_MAX",
    "XP_MIN",
]
