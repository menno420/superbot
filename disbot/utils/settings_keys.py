"""Guild settings key constants — prevents typo drift and documents ownership.

Each key is owned by exactly one subsystem (noted in the comment).
All db.get_setting() / db.set_setting() calls must reference these constants,
never raw string literals.
"""

# XP System (owner: xp_cog)
XP_MIN = "xp_min"
XP_MAX = "xp_max"
XP_COOLDOWN = "xp_cooldown"
XP_ANNOUNCE_CHANNEL = "xp_announce_channel"

# Economy (owner: economy_cog)
ECONOMY_LOG_CHANNEL = "economy_log_channel"

# Moderation (owner: moderation_cog)
WARN_THRESHOLD = "warn_threshold"
WARN_TIMEOUT_MINS = "warn_timeout_minutes"

# Roles (owner: role_cog)
SKIP_ROLES = "skip_roles"

# Games (shared write: rps_tournament_cog + blackjack_cog — see Section 8 of blueprint)
ACTIVE_TOURNAMENT = "active_tournament"

# Governance (owner: governance_service)
# Stores the REGISTRY_VERSION int at which per-guild governance was last upgraded.
GOVERNANCE_VERSION = "governance_version"
# Role ID whose holders are treated as "trusted" tier (ISSUE-015).
TRUSTED_TIER_ROLE_ID = "trusted_tier_role_id"
