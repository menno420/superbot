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

from utils.settings_keys.economy import ECONOMY_LOG_CHANNEL
from utils.settings_keys.games import ACTIVE_TOURNAMENT
from utils.settings_keys.governance import GOVERNANCE_VERSION, TRUSTED_TIER_ROLE_ID
from utils.settings_keys.moderation import WARN_THRESHOLD, WARN_TIMEOUT_MINS
from utils.settings_keys.role import SKIP_ROLES
from utils.settings_keys.xp import (
    XP_ANNOUNCE_CHANNEL,
    XP_COOLDOWN,
    XP_MAX,
    XP_MIN,
)

__all__ = [
    "ACTIVE_TOURNAMENT",
    "ECONOMY_LOG_CHANNEL",
    "GOVERNANCE_VERSION",
    "SKIP_ROLES",
    "TRUSTED_TIER_ROLE_ID",
    "WARN_THRESHOLD",
    "WARN_TIMEOUT_MINS",
    "XP_ANNOUNCE_CHANNEL",
    "XP_COOLDOWN",
    "XP_MAX",
    "XP_MIN",
]
