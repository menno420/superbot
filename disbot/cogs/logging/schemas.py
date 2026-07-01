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
from services.server_logging_config import (
    DEFAULT_CHANNELS_ENABLED,
    DEFAULT_EVENT_ROUTING,
    DEFAULT_IGNORED_CHANNELS,
    DEFAULT_IGNORED_USERS,
    DEFAULT_MEMBERS_ENABLED,
    DEFAULT_MESSAGES_ENABLED,
    DEFAULT_MODERATION_ENABLED,
    DEFAULT_ROLES_ENABLED,
    DEFAULT_SERVER_ENABLED,
    DEFAULT_VOICE_ENABLED,
    ROUTING_COMBINED,
    ROUTING_PER_CATEGORY,
    VALID_ROUTING,
)
from utils.settings_keys import logging as _log_keys


def _validate_bool(value: object) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"expected bool, got {type(value).__name__}: {value!r}")


def _validate_id_csv(value: object) -> None:
    """Reject non-numeric tokens so a typo'd ignore list fails loudly.

    Mirrors the automod/image-moderation exempt-list validator: the
    tolerant :func:`services.automod_config.parse_id_csv` that powers the
    read model must never raise, so this is the *write*-time gate that
    gives the operator feedback instead of silently dropping a bad id.
    """
    if not isinstance(value, str):
        raise ValueError(f"expected a comma-separated id string, got {value!r}")
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            int(token)
        except ValueError:
            raise ValueError(
                f"'{token}' is not a numeric id — use comma-separated ids",
            ) from None


def _validate_routing(value: object) -> None:
    """Accept only the two recognised routing modes.

    ``combined`` (one channel for every event category) or
    ``per_category`` (each category to its own channel). Rejects non-str
    and unknown tokens so a typo fails loudly at write time rather than
    silently degrading the read model.
    """
    if not isinstance(value, str):
        raise ValueError(f"expected a routing mode string, got {value!r}")
    if value not in VALID_ROUTING:
        raise ValueError(
            f"{value!r} is not a routing mode — use one of {sorted(VALID_ROUTING)}",
        )


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
    # -- Server event logging v1 (Q-0109) -------------------------------
    # Per-category passive-event flags. Each is gated by `enabled` (the
    # master switch above) *and* its own flag; all default OFF so a guild
    # that already runs moderation logging sees no new behaviour.
    SettingSpec(
        name="messages_enabled",
        value_type=bool,
        default=DEFAULT_MESSAGES_ENABLED,
        settings_key=_log_keys.LOGGING_MESSAGES_ENABLED,
        capability_required="logging.settings.configure",
        hint=(
            "Log message edits and deletions to the configured channel.  "
            "⚠️ Privacy: when on, staff can see the content of messages "
            "that members edited or deleted.  Off by default."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="members_enabled",
        value_type=bool,
        default=DEFAULT_MEMBERS_ENABLED,
        settings_key=_log_keys.LOGGING_MEMBERS_ENABLED,
        capability_required="logging.settings.configure",
        hint="Log member joins and departures (account age, member count, roles held).",
        validator=_validate_bool,
    ),
    SettingSpec(
        name="roles_enabled",
        value_type=bool,
        default=DEFAULT_ROLES_ENABLED,
        settings_key=_log_keys.LOGGING_ROLES_ENABLED,
        capability_required="logging.settings.configure",
        hint="Log role grants and revocations on members (which roles were added/removed).",
        validator=_validate_bool,
    ),
    # -- Server event logging v2 (Discord audit-log integration) ---------
    # New categories sourced from the Discord audit log — they capture
    # administrative actions taken by *anyone* (native UI, another bot, or
    # SuperBot), with the actor named, closing the "Dyno catches things we
    # don't" gap. `voice` is a passive gateway event (not audit-log). All
    # default OFF and require the bot to hold **View Audit Log** (except
    # voice); see `!logging status`.
    SettingSpec(
        name="moderation_enabled",
        value_type=bool,
        default=DEFAULT_MODERATION_ENABLED,
        settings_key=_log_keys.LOGGING_MODERATION_ENABLED,
        capability_required="logging.settings.configure",
        hint=(
            "Log moderation actions from the Discord audit log — bans, unbans, "
            "kicks, timeouts, prunes, and voice disconnects/moves — taken by "
            "anyone (native UI, another bot, or SuperBot), with the actor "
            "named.  Requires the bot's **View Audit Log** permission."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="channels_enabled",
        value_type=bool,
        default=DEFAULT_CHANNELS_ENABLED,
        settings_key=_log_keys.LOGGING_CHANNELS_ENABLED,
        capability_required="logging.settings.configure",
        hint=(
            "Log channel and permission changes from the audit log — channel "
            "create/delete/update, permission overwrites, threads, and stages.  "
            "Requires the bot's **View Audit Log** permission."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="server_enabled",
        value_type=bool,
        default=DEFAULT_SERVER_ENABLED,
        settings_key=_log_keys.LOGGING_SERVER_ENABLED,
        capability_required="logging.settings.configure",
        hint=(
            "Log server-structure changes from the audit log — server settings, "
            "role definitions (create/rename/delete), emojis, stickers, "
            "webhooks, integrations, and invites.  Requires the bot's **View "
            "Audit Log** permission."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="voice_enabled",
        value_type=bool,
        default=DEFAULT_VOICE_ENABLED,
        settings_key=_log_keys.LOGGING_VOICE_ENABLED,
        capability_required="logging.settings.configure",
        hint=(
            "Log voice-channel joins, leaves, and moves (bots excluded).  "
            "Passive gateway event — no audit-log permission needed."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="event_routing",
        value_type=str,
        default=DEFAULT_EVENT_ROUTING,
        settings_key=_log_keys.LOGGING_EVENT_ROUTING,
        capability_required="logging.settings.configure",
        hint=(
            "How event logs are routed: `combined` sends every category to "
            "one channel (the events route); `per_category` sends each to "
            "its own (messages / members / roles), falling back to the "
            "combined channel when a category channel is unset."
        ),
        validator=_validate_routing,
        allowed_values=(ROUTING_COMBINED, ROUTING_PER_CATEGORY),
    ),
    # -- Exclusion lists (completion cert punch #1) ---------------------
    # Comma-separated id CSV; a passive event whose channel/subject id is
    # listed is never logged, for every category. Both default empty (no
    # exclusion) so every existing guild is byte-identical.
    SettingSpec(
        name="ignored_channels",
        value_type=str,
        default=DEFAULT_IGNORED_CHANNELS,
        settings_key=_log_keys.LOGGING_IGNORED_CHANNELS,
        capability_required="logging.settings.configure",
        hint=(
            "Comma-separated channel ids the event log ignores — an event "
            "in one of these channels is never logged (e.g. a staff-testing "
            "or bot-command channel).  Leave empty to log every channel."
        ),
        validator=_validate_id_csv,
    ),
    SettingSpec(
        name="ignored_users",
        value_type=str,
        default=DEFAULT_IGNORED_USERS,
        settings_key=_log_keys.LOGGING_IGNORED_USERS,
        capability_required="logging.settings.configure",
        hint=(
            "Comma-separated user ids the event log ignores — edits/deletes, "
            "joins/leaves, and role changes for these members are never "
            "logged (e.g. other bots).  Leave empty to log every member."
        ),
        validator=_validate_id_csv,
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
    # Server event logging v1 (Q-0109) — passive-event channel slots.
    # ``events_channel`` is the combined "everything" destination; the
    # three per-category slots fall back to it (NOT to ``mod_channel``) so
    # event noise never lands in the moderation-action channel.
    BindingSpec(
        name="events_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Combined channel for all server events (edits/deletes, "
            "joins/leaves, role changes) in `combined` routing mode, and "
            "the per-category fallback in `per_category` mode."
        ),
        capability_required="logging.settings.configure",
    ),
    BindingSpec(
        name="message_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel for message edits/deletions in `per_category` mode.  "
            "Falls back to `events_channel` when unbound."
        ),
        capability_required="logging.settings.configure",
    ),
    BindingSpec(
        name="member_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel for member joins/leaves in `per_category` mode.  "
            "Falls back to `events_channel` when unbound."
        ),
        capability_required="logging.settings.configure",
    ),
    BindingSpec(
        name="role_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel for role grants/revocations in `per_category` mode.  "
            "Falls back to `events_channel` when unbound."
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
    # Server event logging v1 (Q-0109) — RECOMMENDED requirements for the
    # passive-event routes.  Names mirror the DEFAULT_*_CHANNEL_NAME
    # constants in ``utils.settings_keys.logging`` so the create-channel
    # flow and the auto-create fallback agree.
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="events_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="bot-event-log",
            suggested_category="Staff",
        ),
        binding_name="events_channel",
        description=("Combined channel for server events (edits/joins/roles)."),
    ),
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="message_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="bot-message-log",
            suggested_category="Staff",
        ),
        binding_name="message_channel",
        description=("Per-category channel for message edits/deletions."),
    ),
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="member_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="bot-member-log",
            suggested_category="Staff",
        ),
        binding_name="member_channel",
        description=("Per-category channel for member joins/leaves."),
    ),
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="role_log",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.RECOMMENDED,
            suggested_name="bot-role-log",
            suggested_category="Staff",
        ),
        binding_name="role_channel",
        description=("Per-category channel for role grants/revocations."),
    ),
)


LOGGING_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="logging",
    settings=LOGGING_SETTINGS,
    bindings=LOGGING_BINDINGS,
    resource_requirements=LOGGING_RESOURCE_REQUIREMENTS,
    # v2 (Phase 9a): added debug/info/warning/error/audit channel
    # bindings + matching RECOMMENDED resource requirements.
    # v3 (server event logging v1, Q-0109): added the messages/members/
    # roles category flags + event_routing mode setting, the
    # events/message/member/role channel bindings, and their RECOMMENDED
    # resource requirements.
    # v4 (completion cert punch #1): added the ignored_channels /
    # ignored_users exclusion-list scalar settings.
    # v5 (server event logging v2 — audit-log integration): added the
    # moderation / channels / server / voice category flags. The audit-log
    # categories reuse the combined `events_channel` route (no new bindings);
    # `roles` is repurposed to the audit-log path for actor attribution.
    version=5,
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
