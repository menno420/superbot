"""XP subsystem schemas — Phase 1 reference migration.

The XP cog is the first subsystem to declare the full Phase 1 surface:
guild config schema (P1a), participation schema (P1b), and resource
requirements (P1c).  Other subsystems will mirror this pattern as they
migrate.

The schemas are registered in :meth:`cogs.xp_cog.XpCog.cog_load`; they
are reachable from this module without instantiating the cog so the
wizard (Phase 7) can render setup screens for the subsystem even when
the cog itself failed to load (INV-J).
"""

from __future__ import annotations

from core.runtime.participation_schema import (
    NotificationIntent,
    ParticipationSchema,
    PreferenceSpec,
    PreferenceValueType,
    SubscriptionSpec,
    VisibilityIntent,
)
from core.runtime.resource_specs import (
    ProvisioningHint,
    ProvisioningPriority,
    ResourceKind,
    ResourceRequirement,
)
from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SettingSpec,
    SubsystemSchema,
)
from utils.settings_keys import (
    XP_ANNOUNCE_CHANNEL,
    XP_COOLDOWN,
    XP_MAX,
    XP_MIN,
)


def _validate_positive_int(value: object) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"expected positive int, got {value!r}")


def _validate_cooldown(value: object) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"expected non-negative int cooldown, got {value!r}")


def _validate_channel_id_or_empty(value: object) -> None:
    """Empty string clears the announce channel; otherwise a numeric ID."""
    if not isinstance(value, str):
        raise ValueError(f"expected str, got {type(value).__name__}")
    if value and not value.isdigit():
        raise ValueError(
            "must be empty (to clear) or a numeric Discord channel ID",
        )


# ---------------------------------------------------------------------------
# Phase 1a — Guild config schema
# ---------------------------------------------------------------------------

XP_BINDINGS: tuple[BindingSpec, ...] = (
    BindingSpec(
        name="announce_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel where XP level-up announcements post.  Leave unbound to "
            "announce in the channel where the level-up happened."
        ),
        capability_required="xp.settings.configure",
    ),
)

XP_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="xp_min",
        value_type=int,
        default=15,
        settings_key=XP_MIN,
        capability_required="xp.settings.configure",
        hint="Minimum XP awarded per qualifying message.",
        validator=_validate_positive_int,
    ),
    SettingSpec(
        name="xp_max",
        value_type=int,
        default=25,
        settings_key=XP_MAX,
        capability_required="xp.settings.configure",
        hint="Maximum XP awarded per qualifying message.",
        validator=_validate_positive_int,
    ),
    SettingSpec(
        name="xp_cooldown",
        value_type=int,
        default=60,
        settings_key=XP_COOLDOWN,
        capability_required="xp.settings.configure",
        hint=(
            "Seconds between XP awards per user.  Zero disables the "
            "cooldown (not recommended in active guilds)."
        ),
        validator=_validate_cooldown,
        # PR #7 — Settings edit dispatcher picks the preset row when
        # the hint is "numeric_presets" and ``presets`` is non-empty.
        # Operators still get the free-form modal via the "Override…"
        # button so values outside the preset set remain reachable.
        input_hint="numeric_presets",
        presets=(0, 15, 30, 60, 120, 300),
    ),
    SettingSpec(
        name="xp_announce_channel",
        value_type=str,
        default="",
        settings_key=XP_ANNOUNCE_CHANNEL,
        capability_required="xp.settings.configure",
        hint=(
            "Numeric Discord channel ID for level-up announcements.  "
            "Leave empty to announce in the channel where the level-up "
            "happened."
        ),
        validator=_validate_channel_id_or_empty,
        # PR #7 — opt in to the native channel select.  The Settings
        # edit dispatcher renders a discord.ui.ChannelSelect; the
        # legacy text-modal fallback is still reachable when the spec
        # is mutated programmatically (the SettingSpec.value_type is
        # still str so the pipeline accepts either shape).
        input_hint="channel",
    ),
)

XP_RESOURCE_REQUIREMENTS: tuple[ResourceRequirement, ...] = (
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="announce_channel",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.OPTIONAL,
            suggested_name="level-ups",
            suggested_category="Community",
        ),
        binding_name="announce_channel",
        description=(
            "Dedicated channel for level-up announcements.  Optional — "
            "XP announces in-place when this is unset."
        ),
    ),
)

XP_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="xp",
    bindings=XP_BINDINGS,
    settings=XP_SETTINGS,
    resource_requirements=XP_RESOURCE_REQUIREMENTS,
    version=1,
)


# ---------------------------------------------------------------------------
# Phase 1b — Participation schema
# ---------------------------------------------------------------------------

XP_SUBSCRIPTIONS: tuple[SubscriptionSpec, ...] = (
    SubscriptionSpec(
        name="participation",
        description=(
            "Whether the user earns XP from their messages.  Disabling "
            "this opts the user out of the XP system entirely."
        ),
        default_enabled=True,
        requires_optin=False,
    ),
)

XP_VISIBILITY_INTENTS: tuple[VisibilityIntent, ...] = (
    VisibilityIntent(
        name="xp.leaderboard.public",
        description=(
            "Whether this user appears on the public XP leaderboard.  "
            "Disabling hides the user from the leaderboard but does NOT "
            "stop them from earning XP."
        ),
        default_enabled=True,
    ),
    VisibilityIntent(
        name="xp.rank.public",
        description=(
            "Whether this user's rank is visible when other members "
            "look them up via ``!rank``."
        ),
        default_enabled=True,
    ),
)

XP_NOTIFICATION_INTENTS: tuple[NotificationIntent, ...] = (
    NotificationIntent(
        name="xp.levelup",
        description=(
            "Direct-message notifications when the user levels up.  "
            "Suppressed by default; users opt in via /myprofile."
        ),
        default_enabled=False,
        digestable=True,
    ),
)

XP_PREFERENCE_SPECS: tuple[PreferenceSpec, ...] = (
    PreferenceSpec(
        name="rank_embed_style",
        description="Visual style for the !rank embed.",
        value_type=PreferenceValueType.ENUM,
        default="standard",
        allowed_values=("standard", "compact", "rich"),
    ),
)

XP_PARTICIPATION_SCHEMA = ParticipationSchema(
    subsystem="xp",
    subscriptions=XP_SUBSCRIPTIONS,
    visibility_intents=XP_VISIBILITY_INTENTS,
    notification_intents=XP_NOTIFICATION_INTENTS,
    preference_specs=XP_PREFERENCE_SPECS,
    version=1,
)


def register_schemas() -> None:
    """Register every Phase 1 schema for the XP subsystem.

    Called from :meth:`cogs.xp_cog.XpCog.cog_load`; idempotent so
    hot-reloading the cog re-registers cleanly.
    """
    from core.runtime import participation_schema, subsystem_schema

    subsystem_schema.register(XP_CONFIG_SCHEMA)
    participation_schema.register(XP_PARTICIPATION_SCHEMA)


__all__ = [
    "XP_CONFIG_SCHEMA",
    "XP_PARTICIPATION_SCHEMA",
    "register_schemas",
]
