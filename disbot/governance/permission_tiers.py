"""Phase 1d — Typed permission tier metadata.

The governance runtime already uses tier *strings* (``"user"``,
``"trusted"``, ``"staff"``, ``"moderator"``, ``"administrator"``,
``"owner"``) — see :data:`utils.visibility_rules` and the
``visibility_tier`` field on :data:`utils.subsystem_registry.SUBSYSTEMS`
entries.

Phase 1d formalizes the taxonomy as a :class:`PermissionTier` enum
with rich metadata (description, inheritance hint, recommended roles)
so Phase 4.5's role-template provisioning and Phase 7's wizard can:

* Render the tier list with descriptions (not bare strings).
* Cross-reference recommended Discord roles per tier.
* Statically validate role-template bindings.

The string values match the historical names, so existing code paths
that store/read the bare strings keep working unchanged.  The
:func:`tier_index` helper exposes the inherited ordering for
:func:`utils.visibility_rules.is_tier_sufficient` checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PermissionTier(Enum):
    """Typed taxonomy of platform permission tiers.

    Tier ordering (broadest → strictest):

        USER → TRUSTED → STAFF → MODERATOR → ADMINISTRATOR → OWNER

    A holder of tier N is implicitly granted every capability scoped
    to tiers ≤ N.  Phase 4.5's :class:`access_control_service` resolves
    capability authority through this ordering.

    A separate :class:`PermissionTier.PLATFORM_OWNER` is reserved for
    feature-flag mutations, environment-tier assignments, and cross-
    guild template publishing (Phase 2d / Phase 8).  Holders are NOT
    discoverable via Discord permissions; the platform owner is
    declared at deploy time via an env-var-allowlist —
    :data:`config.BOT_OWNER_USER_ID`, tested by the single-source
    helper :func:`config.is_platform_owner`.  That helper also grants
    the platform owner **full bot-configuration authority in any guild
    they are a member of** (every authority seam — governance capability/
    visibility, the service mutation gates, setup access, and the view
    admin gates — routes its owner check through it), so the bot owner
    can always set the bot up correctly regardless of their server role.
    """

    USER = "user"
    TRUSTED = "trusted"
    STAFF = "staff"
    MODERATOR = "moderator"
    ADMINISTRATOR = "administrator"
    OWNER = "owner"
    PLATFORM_OWNER = "platform_owner"


# Ordered list — index is the implicit "rank" used by tier comparisons.
_TIER_ORDER: tuple[PermissionTier, ...] = (
    PermissionTier.USER,
    PermissionTier.TRUSTED,
    PermissionTier.STAFF,
    PermissionTier.MODERATOR,
    PermissionTier.ADMINISTRATOR,
    PermissionTier.OWNER,
    PermissionTier.PLATFORM_OWNER,
)


@dataclass(frozen=True)
class PermissionTierMeta:
    """Rich metadata for a permission tier."""

    tier: PermissionTier
    tier_index: int
    description: str
    inherits_from: PermissionTier | None
    recommended_role_names: tuple[str, ...]


_TIER_METADATA: dict[PermissionTier, PermissionTierMeta] = {
    PermissionTier.USER: PermissionTierMeta(
        tier=PermissionTier.USER,
        tier_index=0,
        description="Any guild member.  No elevated permissions.",
        inherits_from=None,
        recommended_role_names=(),
    ),
    PermissionTier.TRUSTED: PermissionTierMeta(
        tier=PermissionTier.TRUSTED,
        tier_index=1,
        description=(
            "Members the guild has chosen to extend modest trust to "
            "(e.g. veterans, donors).  Bound via the "
            "``TRUSTED_TIER_ROLE_ID`` setting."
        ),
        inherits_from=PermissionTier.USER,
        recommended_role_names=("Trusted", "Veteran", "Member+"),
    ),
    PermissionTier.STAFF: PermissionTierMeta(
        tier=PermissionTier.STAFF,
        tier_index=2,
        description=(
            "Non-moderation staff with elevated access to "
            "subsystem-specific surfaces (e.g. event organizers)."
        ),
        inherits_from=PermissionTier.TRUSTED,
        recommended_role_names=("Staff", "Organizer", "Helper"),
    ),
    PermissionTier.MODERATOR: PermissionTierMeta(
        tier=PermissionTier.MODERATOR,
        tier_index=3,
        description=(
            "Members authorized to enforce community rules — warns, "
            "timeouts, kicks.  Minimum tier for governance writes."
        ),
        inherits_from=PermissionTier.STAFF,
        recommended_role_names=("Moderator", "Mod"),
    ),
    PermissionTier.ADMINISTRATOR: PermissionTierMeta(
        tier=PermissionTier.ADMINISTRATOR,
        tier_index=4,
        description=(
            "Server administrators — full configuration authority, "
            "including subsystem visibility and cleanup policy."
        ),
        inherits_from=PermissionTier.MODERATOR,
        recommended_role_names=("Administrator", "Admin"),
    ),
    PermissionTier.OWNER: PermissionTierMeta(
        tier=PermissionTier.OWNER,
        tier_index=5,
        description=(
            "Discord guild owner.  Resolved via "
            ":data:`guild.owner_id`; no role mapping needed."
        ),
        inherits_from=PermissionTier.ADMINISTRATOR,
        recommended_role_names=(),
    ),
    PermissionTier.PLATFORM_OWNER: PermissionTierMeta(
        tier=PermissionTier.PLATFORM_OWNER,
        tier_index=6,
        description=(
            "Reserved for platform-level operations: feature flag "
            "mutation, environment-tier assignment, cross-guild "
            "template publishing.  Not discoverable via Discord "
            "permissions; declared at deploy time."
        ),
        inherits_from=PermissionTier.OWNER,
        recommended_role_names=(),
    ),
}


def metadata_for(tier: PermissionTier) -> PermissionTierMeta:
    """Return rich metadata for ``tier``."""
    return _TIER_METADATA[tier]


def tier_index(tier: PermissionTier | str) -> int:
    """Return the implicit rank of ``tier`` (USER=0 .. PLATFORM_OWNER=6).

    Accepts either an enum or a legacy string for back-compat.  Raises
    ``ValueError`` on unknown input.
    """
    if isinstance(tier, str):
        try:
            tier = PermissionTier(tier)
        except ValueError:
            valid = ", ".join(t.value for t in PermissionTier)
            raise ValueError(
                f"unknown permission tier {tier!r}; valid: {valid}",
            ) from None
    return _TIER_METADATA[tier].tier_index


def tier_at_or_above(
    holder: PermissionTier | str,
    required: PermissionTier | str,
) -> bool:
    """Return True iff ``holder`` ranks at or above ``required``."""
    return tier_index(holder) >= tier_index(required)


def all_tiers_ordered() -> tuple[PermissionTier, ...]:
    """Return the tier list in ascending rank order."""
    return _TIER_ORDER


__all__ = [
    "PermissionTier",
    "PermissionTierMeta",
    "all_tiers_ordered",
    "metadata_for",
    "tier_at_or_above",
    "tier_index",
]
