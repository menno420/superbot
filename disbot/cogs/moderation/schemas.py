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
    DEFAULT_DM_ACTIONS,
    DEFAULT_DM_ON_ACTION,
    DEFAULT_DM_TEMPLATE,
    DEFAULT_MAX_TIMEOUT_MINUTES,
    DEFAULT_POST_ACTION_CLEANUP,
    DEFAULT_POST_ACTION_CLEANUP_LIMIT,
    DEFAULT_PUBLIC_LOG_ACTIONS,
    DEFAULT_PUBLIC_LOG_CHANNEL,
    DEFAULT_REQUIRE_REASON,
    DEFAULT_WARN_ESCALATION_ACTION,
    DEFAULT_WARN_THRESHOLD,
    DEFAULT_WARN_TIMEOUT_MINUTES,
    DM_NOTIFY_ACTIONS,
    MAX_BAN_DELETE_MESSAGE_DAYS,
    MAX_POST_ACTION_CLEANUP_LIMIT,
    MAX_TIMEOUT_MINUTES,
    MIN_BAN_DELETE_MESSAGE_DAYS,
    MIN_POST_ACTION_CLEANUP_LIMIT,
    MIN_TIMEOUT_MINUTES,
    POST_ACTION_CLEANUP_ACTIONS,
    PUBLIC_LOG_ACTIONS,
    WARN_ESCALATION_ACTIONS,
)
from utils.settings_keys import (
    MOD_BAN_DELETE_MESSAGE_DAYS,
    MOD_DM_ACTIONS,
    MOD_DM_ON_ACTION,
    MOD_DM_TEMPLATE,
    MOD_MAX_TIMEOUT_MINUTES,
    MOD_POST_ACTION_CLEANUP,
    MOD_POST_ACTION_CLEANUP_LIMIT,
    MOD_PUBLIC_LOG_ACTIONS,
    MOD_PUBLIC_LOG_CHANNEL,
    MOD_REQUIRE_REASON,
    MOD_WARN_ESCALATION_ACTION,
    MODERATOR_TIER_ROLE_ID,
    TRUSTED_TIER_ROLE_ID,
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


def _validate_escalation_action(value: object) -> None:
    if value not in WARN_ESCALATION_ACTIONS:
        raise ValueError(
            "warn_escalation_action must be one of "
            f"{', '.join(WARN_ESCALATION_ACTIONS)}, got {value!r}",
        )


def _validate_post_action_cleanup(value: object) -> None:
    if value not in POST_ACTION_CLEANUP_ACTIONS:
        raise ValueError(
            "post_action_cleanup must be one of "
            f"{', '.join(POST_ACTION_CLEANUP_ACTIONS)}, got {value!r}",
        )


def _validate_post_action_cleanup_limit(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"expected int, got {value!r}")
    if not (MIN_POST_ACTION_CLEANUP_LIMIT <= value <= MAX_POST_ACTION_CLEANUP_LIMIT):
        raise ValueError(
            "post_action_cleanup_limit must be between "
            f"{MIN_POST_ACTION_CLEANUP_LIMIT} and {MAX_POST_ACTION_CLEANUP_LIMIT}",
        )


def _validate_dm_actions(value: object) -> None:
    """Accept a comma-separated subset of the notify-eligible actions.

    Empty (no action DMs) is allowed; every non-empty token must be one of
    :data:`DM_NOTIFY_ACTIONS` (warn / timeout / kick / ban).  An unknown token
    is rejected rather than silently dropped here, so the operator gets a clear
    error at edit time (the runtime ``parse_dm_actions`` stays fail-safe).
    """
    if not isinstance(value, str):
        raise ValueError(f"expected str, got {type(value).__name__}")
    known = set(DM_NOTIFY_ACTIONS)
    tokens = [t.strip().lower() for t in value.split(",") if t.strip()]
    unknown = [t for t in tokens if t not in known]
    if unknown:
        raise ValueError(
            "dm_actions must be a comma-separated subset of "
            f"{', '.join(DM_NOTIFY_ACTIONS)}; unknown: {', '.join(unknown)}",
        )


def _validate_public_log_actions(value: object) -> None:
    if value not in PUBLIC_LOG_ACTIONS:
        raise ValueError(
            "public_log_actions must be one of "
            f"{', '.join(PUBLIC_LOG_ACTIONS)}, got {value!r}",
        )


def _validate_public_log_channel(value: object) -> None:
    """Accept an empty string (off) or a numeric channel id."""
    if not isinstance(value, str):
        raise ValueError(f"expected str, got {type(value).__name__}")
    text = value.strip()
    if text and not text.isdigit():
        raise ValueError(
            f"public_log_channel must be empty or a numeric channel id, got {value!r}",
        )


def _validate_role_id_or_empty(value: object) -> None:
    """Accept an empty string (unset) or a numeric role id."""
    if not isinstance(value, str):
        raise ValueError(f"expected str, got {type(value).__name__}")
    text = value.strip()
    if text and not text.isdigit():
        raise ValueError(
            f"role setting must be empty or a numeric role id, got {value!r}",
        )


# ---------------------------------------------------------------------------
# Phase 1a — Guild config schema
# ---------------------------------------------------------------------------

MODERATION_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="warn_threshold",
        value_type=int,
        default=DEFAULT_WARN_THRESHOLD,
        settings_key=WARN_THRESHOLD,
        capability_required="moderation.settings.configure",
        hint=(
            "Number of warnings before the escalation action is applied.  "
            "Set high to effectively disable automatic escalation."
        ),
        validator=_validate_positive_int,
    ),
    SettingSpec(
        name="warn_timeout_minutes",
        value_type=int,
        default=DEFAULT_WARN_TIMEOUT_MINUTES,
        settings_key=WARN_TIMEOUT_MINS,
        capability_required="moderation.settings.configure",
        hint=(
            "Duration in minutes of the automatic timeout triggered when "
            "warn_threshold is reached and warn_escalation_action is 'timeout'."
        ),
        validator=_validate_positive_int,
    ),
    SettingSpec(
        name="warn_escalation_action",
        value_type=str,
        default=DEFAULT_WARN_ESCALATION_ACTION,
        settings_key=MOD_WARN_ESCALATION_ACTION,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "What happens when a member reaches warn_threshold warnings: "
            "'timeout' (the default — auto-timeout for warn_timeout_minutes, "
            "then reset), 'kick', 'ban', or 'none' to disable auto-escalation."
        ),
        validator=_validate_escalation_action,
        allowed_values=WARN_ESCALATION_ACTIONS,
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
            "Master switch for notifying members by DM.  When on, the actions "
            "listed in 'dm_actions' DM the affected member a notice (the action "
            "+ reason) — when off, no moderation DM is ever sent.  Best-effort: "
            "silently skipped when the member has DMs closed."
        ),
        validator=_validate_bool,
    ),
    SettingSpec(
        name="dm_actions",
        value_type=str,
        default=DEFAULT_DM_ACTIONS,
        settings_key=MOD_DM_ACTIONS,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "Which actions DM the affected member when 'dm_on_action' is on: a "
            "comma-separated subset of warn, timeout, kick, ban (default all "
            "four).  Narrow it to suppress specific DMs — e.g. 'warn,timeout' "
            "to notify on warnings but not on a kick or ban.  Has no effect "
            "while the 'dm_on_action' master switch is off."
        ),
        validator=_validate_dm_actions,
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
        name="require_reason",
        value_type=bool,
        default=DEFAULT_REQUIRE_REASON,
        settings_key=MOD_REQUIRE_REASON,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "Require a non-empty reason for warn / kick / ban.  When on, the "
            "action is rejected (at the moderation_service seam) if no reason "
            "is given.  Timeout is exempt — its reason carries the duration."
        ),
        validator=_validate_bool,
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
    # PR10 fourth slice — optional post-action message cleanup, requested
    # from the cleanup subsystem at the ``moderation_service`` seam.
    SettingSpec(
        name="post_action_cleanup",
        value_type=str,
        default=DEFAULT_POST_ACTION_CLEANUP,
        settings_key=MOD_POST_ACTION_CLEANUP,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "After a kick or ban, sweep the member's recent messages in the "
            "channel where the action was taken: 'none' (default), 'kick', "
            "'ban', or 'both'.  The bot needs Manage Messages + Read Message "
            "History in that channel."
        ),
        validator=_validate_post_action_cleanup,
        allowed_values=POST_ACTION_CLEANUP_ACTIONS,
    ),
    SettingSpec(
        name="post_action_cleanup_limit",
        value_type=int,
        default=DEFAULT_POST_ACTION_CLEANUP_LIMIT,
        settings_key=MOD_POST_ACTION_CLEANUP_LIMIT,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "How many recent messages to scan for the post-action cleanup "
            "sweep (1–500).  Only the moderated member's messages within that "
            "scan window are removed."
        ),
        validator=_validate_post_action_cleanup_limit,
        input_hint="numeric_presets",
        presets=(50, 100, 200, 500),
    ),
    # PR10 fifth slice — optional PUBLIC moderation log (operator opt-in;
    # announces selected actions without naming the acting moderator).
    SettingSpec(
        name="public_log_actions",
        value_type=str,
        default=DEFAULT_PUBLIC_LOG_ACTIONS,
        settings_key=MOD_PUBLIC_LOG_ACTIONS,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "Which actions are announced in the public moderation log: 'none' "
            "(default, off), 'bans', 'removals' (kick + ban), or 'all' (warn + "
            "timeout + kick + ban).  The acting moderator is never shown "
            "publicly.  Requires public_log_channel to be set."
        ),
        validator=_validate_public_log_actions,
        allowed_values=PUBLIC_LOG_ACTIONS,
    ),
    SettingSpec(
        name="public_log_channel",
        value_type=str,
        default=DEFAULT_PUBLIC_LOG_CHANNEL,
        settings_key=MOD_PUBLIC_LOG_CHANNEL,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "Channel for the optional public moderation log.  Leave empty to "
            "disable.  Public entries show the action, the affected member, and "
            "the reason — but never which moderator acted."
        ),
        validator=_validate_public_log_channel,
        input_hint="channel",
    ),
    # PR10 final slice — capability-native moderator / trusted roles (ADR-008).
    # Setting a role here grants its members the corresponding governance tier
    # via governance.resolver._resolve_member_tier, so non-admins can moderate
    # (moderator role) or reach trust-gated surfaces (trusted role).  Stored as
    # the numeric role id (string), read back through config_arbitration.
    # Changing them requires the administrator floor (``moderation.settings.
    # configure``) — only admins decide who moderates.  The grant only ever
    # *adds* standing; a member keeps any access their Discord permissions
    # already give them.
    SettingSpec(
        name="moderator_role",
        value_type=str,
        default="",
        settings_key=MODERATOR_TIER_ROLE_ID,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "Role whose members may use moderation actions (warn, timeout, "
            "kick, ban) without holding Discord moderation permissions.  Leave "
            "empty to require Discord permissions only.  This only adds access — "
            "no one who can moderate today loses it."
        ),
        validator=_validate_role_id_or_empty,
        input_hint="role",
    ),
    SettingSpec(
        name="trusted_role",
        value_type=str,
        default="",
        settings_key=TRUSTED_TIER_ROLE_ID,
        capability_required=_MODERATION_CAPABILITY,
        hint=(
            "Role whose members are treated as the 'trusted' tier — reserved "
            "for trust-gated features and surfaces.  Leave empty to disable.  "
            "Like the moderator role, this only ever adds standing."
        ),
        validator=_validate_role_id_or_empty,
        input_hint="role",
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
    # v3 — PR10 third slice added warn_escalation_action (configurable terminal
    # escalation, owned at the moderation_service warn seam).
    # v4 — PR10 fourth slice added post_action_cleanup / post_action_cleanup_limit
    # (optional post-kick/ban message sweep, requested from the cleanup service).
    # v5 — PR10 fifth slice added public_log_actions / public_log_channel (optional
    # operator-opt-in public moderation log, delivered by services.server_logging).
    # v6 — PR10 final slice added moderator_role / trusted_role (capability-native
    # authority — a configured role grants the moderator / trusted tier; ADR-008).
    # v7 — Q-0147 added dm_actions (per-action DM allow-list gating the existing
    # dm_on_action master switch; default = all four notify-eligible actions, so
    # the master switch keeps today's behaviour and an owner narrows it).
    version=7,
)


def register_schemas() -> None:
    """Register Phase 1 schemas for the moderation subsystem."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(MODERATION_CONFIG_SCHEMA)


__all__ = [
    "MODERATION_CONFIG_SCHEMA",
    "register_schemas",
]
