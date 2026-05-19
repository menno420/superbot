"""Economy subsystem schemas — Phase 1 reference migration.

Declares the guild config schema for the economy subsystem.  A
participation schema is intentionally deferred to Phase 2c-era follow-up
work: economy's per-user state today lives in the ``economy_balances``
table (game state, not platform participation), so participation
declarations would describe future opt-in flows (daily-reminder DMs,
shop digest preferences) rather than today's behavior.
"""

from __future__ import annotations

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
from utils.settings_keys import ECONOMY_LOG_CHANNEL


def _validate_channel_id_or_empty(value: object) -> None:
    """Empty string clears the log channel; otherwise a numeric ID."""
    if not isinstance(value, str):
        raise ValueError(f"expected str, got {type(value).__name__}")
    if value and not value.isdigit():
        raise ValueError(
            "must be empty (to clear) or a numeric Discord channel ID",
        )


# ---------------------------------------------------------------------------
# Phase 1a — Guild config schema
# ---------------------------------------------------------------------------

ECONOMY_BINDINGS: tuple[BindingSpec, ...] = (
    BindingSpec(
        name="log_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel where economy mutations (work, daily, shop, transfer) "
            "are logged.  Leave unbound to suppress logging."
        ),
        capability_required="economy.settings.configure",
    ),
)

ECONOMY_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="economy_log_channel",
        value_type=str,
        default="",
        settings_key=ECONOMY_LOG_CHANNEL,
        capability_required="economy.settings.configure",
        hint=(
            "Numeric Discord channel ID for the economy mutations log.  "
            "Leave empty to suppress logging.  Mirrors the "
            "``log_channel`` BindingSpec — reads go through the "
            "binding/legacy arbitration ladder; PR #6 routes writes "
            "through SettingsMutationPipeline so they land in the "
            "settings_mutation_audit trail."
        ),
        validator=_validate_channel_id_or_empty,
        # PR #7 — opt in to the native channel select.  Operators
        # pick the channel from Discord's UI instead of pasting a
        # numeric ID into a text modal.
        input_hint="channel",
    ),
)

ECONOMY_RESOURCE_REQUIREMENTS: tuple[ResourceRequirement, ...] = (
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="log_channel",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="economy-log",
            suggested_category="Staff",
        ),
        binding_name="log_channel",
        description=(
            "Operator-facing audit channel for economy mutations.  "
            "Recommended for any guild that runs the economy actively."
        ),
    ),
)

ECONOMY_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="economy",
    bindings=ECONOMY_BINDINGS,
    settings=ECONOMY_SETTINGS,
    resource_requirements=ECONOMY_RESOURCE_REQUIREMENTS,
    version=1,
)


def register_schemas() -> None:
    """Register Phase 1 schemas for the economy subsystem."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(ECONOMY_CONFIG_SCHEMA)


__all__ = [
    "ECONOMY_CONFIG_SCHEMA",
    "register_schemas",
]
