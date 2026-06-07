"""Settings keys owned by the governance runtime (``governance/``)."""

# Stores the REGISTRY_VERSION int at which per-guild governance was last upgraded.
GOVERNANCE_VERSION = "governance_version"

# Role ID whose holders are treated as "trusted" tier (ISSUE-015).
TRUSTED_TIER_ROLE_ID = "trusted_tier_role_id"

# Role ID whose holders are granted the "moderator" tier — i.e. they may use
# moderation actions (warn/timeout/kick/ban) without holding the corresponding
# Discord permissions.  The grant only *raises* a member's tier; it never lowers
# one resolved from real Discord permissions (capability-native authority, ADR-008).
MODERATOR_TIER_ROLE_ID = "moderator_tier_role_id"
