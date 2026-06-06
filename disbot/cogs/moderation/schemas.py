"""Moderation subsystem schemas — Phase 1 reference migration.

Declares the guild config schema for the moderation subsystem.  Bindings
cover the warn-threshold + warn-timeout settings (today stored as bare
ints in ``guild_settings``); resource requirements name the
recommended mod-log channel.
"""

from __future__ import annotations

from core.runtime.resource_specs import (
    ProvisioningHint,
    ProvisioningPriority,
    ResourceKind,
    ResourceRequirement,
)
from core.runtime.subsystem_schema import (
    SettingSpec,
    SubsystemSchema,
)
from services.moderation_config import (
    DEFAULT_BAN_DELETE_MESSAGE_DAYS,
    DEFAULT_DM_ON_ACTION,
    DEFAULT_DM_TEMPLATE,
    DEFAULT_MAX_TIMEOUT_MINUTES,
    MAX_BAN_DELETE_MESSAGE_DAYS,
    MAX_TIMEOUT_MINUTES,
    MIN_BAN_DELETE_MESSAGE_DAYS,
    MIN_TIMEOUT_MINUTES,
)
from utils.settings_keys import (
    MOD_BAN_DELETE_MESSAGE_DAYS,
    MOD_DM_ON_ACTION,
    MOD_DM_TEMPLATE,
    MOD_MAX_TIMEOUT_MINUTES,
    WARN_THRESHOLD,
    WARN_TIMEOUT_MINS,
)

_MODERATION_CAPABILITY = "moderation.settings.configure"
_DM_TEMPLATE_MAX_LEN = 1500


def _validate_positive_int(value: object) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"expected positive int, got {value!r}")


def _validate_bool(value: object) -> None:
    # ``isinstance(True, int)`` is True, so guard the bool type explicitly.
    if not isinstance(value, bool):
        raise ValueError(f"expected bool, got {value!r}")


def _validate_ban_delete_days(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"expected int, got {value!r}")
    if not (MIN_BAN_DELETE_MESSAGE_DAYS <= value <= MAX_BAN_DELETE_MESSAGE_DAYS):
        raise ValueError(
            "ban_delete_message_days must be between "
            f"{MIN_BAN_DELETE_MESSAGE_DAYS} and {MAX_BAN_DELETE_MESSAGE_DAYS}",
        )


def _validate_timeout_ceiling(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"expected int, got {value!r}")
    if not (MIN_TIMEOUT_MINUTES <= value <= MAX_TIMEOUT_MINUTES):
        raise ValueError(
            "max_timeout_minutes must be between "
            f"{MIN_TIMEOUT_MINUTES} and {MAX_TIMEOUT_MINUTES} (28 days)",
        )


def _validate_dm_template(value: object) -> None:
    if not isinstance(value, str):
        raise ValueError(f"expected str, got {type(value).__name__}")
    if len(value) > _DM_TEMPLATE_MAX_LEN:
        raise ValueError(
            f"dm_template must be at most {_DM_TEMPLATE_MAX_LEN} characters",
        )


# ---------------------------------------------------------------------------
# Phase 1a — Guild config schema
# ---------------------------------------------------------------------------

MODERATION_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="warn_threshold",
        value_type=int,
        default=3,
        settings_key=WARN_THRESHOLD,
        capability_required="moderation.settings.configure",
        hint=(
            "Number of warnings before an automatic timeout is applied.  "
            "Set high to disable automatic escalation."
        ),
        validator=_validate_positive_int,
    ),
    SettingSpec(
        name="warn_timeout_minutes",
        value_type=int,
        default=10,
        settings_key=WARN_TIMEOUT_MINS,
        capability_required="moderation.settings.configure",
        hint="Duration in minutes of the automatic timeout triggered by warn_threshold.",
        validator=_validate_positive_int,
    ),
    # PR10 — first-class moderation behaviour, applied at the
    # ``services.moderation_service`` mutation seam so every surface (prefix
    # commands, panel modals, future hub) honours the same policy.
    SettingSpec(
        name="dm_on_action",
        value_type=bool,
        default=DEFAULT_DM_ON_ACTION,
        settings_key=MOD_DM_ON_ACTION,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "DM the affected member a notice when they are warned, timed "
            "out, kicked, or banned.  Best-effort — silently skipped when "
            "the member has DMs closed."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="dm_template",
        value_type=str,
        default=DEFAULT_DM_TEMPLATE,
        settings_key=MOD_DM_TEMPLATE,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "Custom body for the notify-the-member DM.  Leave empty for the "
            "built-in per-action notice.  Tokens: {guild} {action} {reason} "
            "{user}."
        ),
        validator=_validate_dm_template,
    ),
    SettingSpec(
        name="ban_delete_message_days",
        value_type=int,
        default=DEFAULT_BAN_DELETE_MESSAGE_DAYS,
        settings_key=MOD_BAN_DELETE_MESSAGE_DAYS,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "Days of the banned member's recent messages to purge (0–7).  "
            "0 keeps all messages — today's default."
        ),
        validator=_validate_ban_delete_days,
        input_hint="numeric_presets",
        presets=(0, 1, 7),
    ),
    SettingSpec(
        name="max_timeout_minutes",
        value_type=int,
        default=DEFAULT_MAX_TIMEOUT_MINUTES,
        settings_key=MOD_MAX_TIMEOUT_MINUTES,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "Upper bound (minutes) for any single timeout; longer requests "
            "are clamped down.  Default 40320 = 28 days, Discord's maximum, "
            "so an unconfigured guild is unaffected."
        ),
        validator=_validate_timeout_ceiling,
        input_hint="numeric_presets",
        presets=(60, 1440, 10080, 40320),
    ),
)

MODERATION_RESOURCE_REQUIREMENTS: tuple[ResourceRequirement, ...] = (
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="mod_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="mod-logs",
            suggested_category="Staff",
        ),
        description=(
            "Channel where moderation actions (warn, timeout, kick, ban) "
            "are logged.  Recommended for every moderation-bearing guild."
        ),
    ),
)

MODERATION_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="moderation",
    settings=MODERATION_SETTINGS,
    resource_requirements=MODERATION_RESOURCE_REQUIREMENTS,
    # v2 — PR10 added the dm_on_action / dm_template / ban_delete_message_days
    # / max_timeout_minutes behaviour settings.
    version=2,
)


def register_schemas() -> None:
    """Register Phase 1 schemas for the moderation subsystem."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(MODERATION_CONFIG_SCHEMA)


__all__ = [
    "MODERATION_CONFIG_SCHEMA",
    "register_schemas",
]
