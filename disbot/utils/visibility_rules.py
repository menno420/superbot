"""Visibility tier definitions and synchronous member-tier resolution.

IMPORTANT: This module governs UI/help discoverability only.
Execution authorization is a separate concept resolved in governance_service.resolve_execution().
Do NOT conflate visibility with permission to execute.

Allowed imports: utils.subsystem_registry only.
No async, no DB access, no Discord API calls.
"""

from __future__ import annotations

from utils.subsystem_registry import SUBSYSTEMS

# ---------------------------------------------------------------------------
# Tier ordering
# Named VISIBILITY_TIERS (not TIER_ORDER) to make its scope explicit:
# this is about what appears in UI, not about what a member can execute.
# ---------------------------------------------------------------------------

VISIBILITY_TIERS: list[str] = [
    "user",
    "trusted",
    "staff",
    "moderator",
    "administrator",
    "owner",
]

# Maps tier → Discord guild_permissions attribute name.
# None = no Discord permission required (all members qualify).
TIER_DISCORD_PERMISSION: dict[str, str | None] = {
    "user": None,
    "trusted": None,  # reserved for future trust/progression system
    "staff": "manage_guild",
    "moderator": "moderate_members",
    "administrator": "administrator",
    "owner": None,  # resolved by member.id == guild.owner_id
}

_TIER_INDEX: dict[str, int] = {tier: i for i, tier in enumerate(VISIBILITY_TIERS)}


def get_member_visibility_tier(member, guild_owner_id: int) -> str:
    """Return the highest VISIBILITY_TIER this member qualifies for (synchronous).

    Checks from highest tier downward to find the first match.
    """
    if member.id == guild_owner_id:
        return "owner"
    p = member.guild_permissions
    if p.administrator:
        return "administrator"
    if getattr(p, "moderate_members", False):
        return "moderator"
    if p.manage_guild:
        return "staff"
    return "user"


def is_tier_sufficient(member_tier: str, required_tier: str) -> bool:
    """Return True if member_tier is at least as high as required_tier."""
    member_idx = _TIER_INDEX.get(member_tier, 0)
    required_idx = _TIER_INDEX.get(required_tier, 0)
    return member_idx >= required_idx


def get_subsystems_for_tier(member_tier: str) -> list[str]:
    """Return subsystem names whose visibility_tier ≤ member_tier.

    Excludes subsystems with visibility_mode == 'internal' (never user-facing).
    """
    return [
        name
        for name, meta in SUBSYSTEMS.items()
        if is_tier_sufficient(member_tier, meta.get("visibility_tier", "user"))
        and meta.get("visibility_mode", "normal") != "internal"
        and not meta.get("hidden", False)
    ]
