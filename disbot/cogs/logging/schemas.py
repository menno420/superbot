"""Logging subsystem schema — S7a.

Declares the ``logging`` :class:`SubsystemSchema` so the Settings
Manager hub renders a read-only logging page and so the binding /
provisioning catalogues (S7b / S7c) can discover the channel slots.

What this schema declares
-------------------------

* **Scalar settings** (today): ``enabled`` and ``auto_create_channels``.
  Both point at the existing legacy keys in
  :mod:`utils.settings_keys.logging` via ``settings_key=``, so the
  S6 edit/reset flows can mutate them through
  :class:`SettingsMutationPipeline` without any service changes.

* **Bindings** (declared, not yet wired into the runtime read path):
  ``mod_channel`` and ``cleanup_channel`` — both ``BindingKind.CHANNEL``,
  not required.  S7b introduces the
  :class:`BindingMutationPipeline` write path; today
  :func:`services.server_logging.resolve_log_channel` still reads the
  legacy ``LOGGING_MOD_CHANNEL`` / ``LOGGING_CLEANUP_CHANNEL`` scalar
  keys.  Declaring the bindings now lets the catalogues surface them
  and gives S7b a stable contract to migrate against.

* **Resource requirements**: ``mod_log`` and ``cleanup_log`` channels.
  ``RECOMMENDED`` priority because logging is opt-in by default
  (``logging.enabled`` defaults to False) — auto-provisioning waits
  for S7c.

No behavior change is introduced by S7a.  Registering this schema
adds entries to the customization / settings registry / provisioning
catalogues; the runtime logging service is unchanged.
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
from utils.settings_keys import logging as _log_keys


def _validate_bool(value: object) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"expected bool, got {type(value).__name__}: {value!r}")


# ---------------------------------------------------------------------------
# Scalar settings
# ---------------------------------------------------------------------------

LOGGING_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="enabled",
        value_type=bool,
        default=False,
        settings_key=_log_keys.LOGGING_ENABLED,
        capability_required="logging.settings.configure",
        hint=(
            "Master switch for server-logging.  When off, "
            "moderation/cleanup events are not posted to the configured "
            "log channel."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="auto_create_channels",
        value_type=bool,
        default=False,
        settings_key=_log_keys.LOGGING_AUTO_CREATE_CHANNELS,
        capability_required="logging.settings.configure",
        hint=(
            "When enabled and a configured log channel is missing or "
            "invalid, the service creates a fallback channel "
            "(`bot-mod-log` / `bot-cleanup-log`) on next use.  Off by "
            "default so a fresh install never surprises an admin with "
            "spontaneous channels."
        ),
        validator=_validate_bool,
    ),
)


# ---------------------------------------------------------------------------
# Bindings (S7b will wire the mutation path; S7a only declares)
# ---------------------------------------------------------------------------

LOGGING_BINDINGS: tuple[BindingSpec, ...] = (
    BindingSpec(
        name="mod_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel where non-cleanup moderation events (warn, timeout, "
            "kick, ban) are posted.  Falls back to silent when unbound."
        ),
        capability_required="logging.settings.configure",
    ),
    BindingSpec(
        name="cleanup_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel where cleanup auto-delete events are posted.  "
            "Falls back to `mod_channel` when unbound."
        ),
        capability_required="logging.settings.configure",
    ),
    # Phase 9a — severity/source channel slots. All optional. Unset
    # slots fall through to ``mod_channel`` per
    # ``services.server_logging.resolve_log_channel``. No subscriber
    # currently emits events into these — publisher callsites
    # (``runtime.error_raised``, ``runtime.warning_emitted``,
    # ``audit.action_recorded``) land in a follow-up PR (Phase 9c).
    BindingSpec(
        name="debug_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel for debug-level diagnostic events.  Falls back to "
            "`mod_channel` when unbound."
        ),
        capability_required="logging.settings.configure",
    ),
    BindingSpec(
        name="info_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel for info-level events.  Falls back to `mod_channel` "
            "when unbound."
        ),
        capability_required="logging.settings.configure",
    ),
    BindingSpec(
        name="warning_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel for warning-level events.  Falls back to "
            "`mod_channel` when unbound."
        ),
        capability_required="logging.settings.configure",
    ),
    BindingSpec(
        name="error_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel for error-level events.  Falls back to `mod_channel` "
            "when unbound."
        ),
        capability_required="logging.settings.configure",
    ),
    BindingSpec(
        name="audit_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel for audit-trail records (governance/settings/binding "
            "mutations).  Falls back to `mod_channel` when unbound."
        ),
        capability_required="logging.settings.configure",
    ),
)


# ---------------------------------------------------------------------------
# Resource requirements (consumed by S7c create-channel flow)
# ---------------------------------------------------------------------------

LOGGING_RESOURCE_REQUIREMENTS: tuple[ResourceRequirement, ...] = (
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="mod_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="bot-mod-log",
            suggested_category="Staff",
        ),
        binding_name="mod_channel",
        description=(
            "Operator-facing audit channel for moderation actions.  "
            "Recommended for every guild that runs moderation."
        ),
    ),
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="cleanup_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="bot-cleanup-log",
            suggested_category="Staff",
        ),
        binding_name="cleanup_channel",
        description=(
            "Operator-facing channel for cleanup auto-delete events.  "
            "Falls back to the mod-log channel when unbound."
        ),
    ),
    # Phase 9a — RECOMMENDED severity/source resource requirements.
    # Auto-create stays OFF by default; an operator opts in per channel
    # via the existing provisioning flow.
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="debug_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="bot-debug-log",
            suggested_category="Staff",
        ),
        binding_name="debug_channel",
        description=("Operator-facing channel for debug-level diagnostic events."),
    ),
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="info_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="bot-info-log",
            suggested_category="Staff",
        ),
        binding_name="info_channel",
        description=("Operator-facing channel for info-level events."),
    ),
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="warning_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="bot-warning-log",
            suggested_category="Staff",
        ),
        binding_name="warning_channel",
        description=("Operator-facing channel for warning-level events."),
    ),
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="error_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="bot-error-log",
            suggested_category="Staff",
        ),
        binding_name="error_channel",
        description=("Operator-facing channel for error-level events."),
    ),
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="audit_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="bot-audit-log",
            suggested_category="Staff",
        ),
        binding_name="audit_channel",
        description=("Operator-facing channel for audit-trail records."),
    ),
)


LOGGING_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="logging",
    settings=LOGGING_SETTINGS,
    bindings=LOGGING_BINDINGS,
    resource_requirements=LOGGING_RESOURCE_REQUIREMENTS,
    # v2 (Phase 9a): added debug/info/warning/error/audit channel
    # bindings + matching RECOMMENDED resource requirements.
    version=2,
)


def register_schemas() -> None:
    """Register S7a schemas for the logging subsystem.

    Called from :meth:`AdminCog.cog_load` because the ``!logging``
    command group currently lives in :mod:`cogs.admin_cog`.  S7d may
    extract a dedicated ``LoggingCog`` and move this call there.
    """
    from core.runtime import subsystem_schema

    subsystem_schema.register(LOGGING_CONFIG_SCHEMA)


__all__ = [
    "LOGGING_CONFIG_SCHEMA",
    "LOGGING_BINDINGS",
    "LOGGING_RESOURCE_REQUIREMENTS",
    "LOGGING_SETTINGS",
    "register_schemas",
]
