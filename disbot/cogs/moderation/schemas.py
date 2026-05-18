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
from utils.settings_keys import WARN_THRESHOLD, WARN_TIMEOUT_MINS


def _validate_positive_int(value: object) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"expected positive int, got {value!r}")


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
    version=1,
)


def register_schemas() -> None:
    """Register Phase 1 schemas for the moderation subsystem."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(MODERATION_CONFIG_SCHEMA)


__all__ = [
    "MODERATION_CONFIG_SCHEMA",
    "register_schemas",
]
