"""Automation templates — Phase 9h / Track 7 PR 19.

Operator-friendly preset constructors for the automation
substrate. Each template returns a typed
:class:`AutomationTemplate` that the wizard hub (Track 8) can
hand to
:class:`services.automation_mutation.AutomationMutationPipeline.create_rule`.

Templates own:

* A stable ``slug`` so the wizard can list / search by name.
* A ``display_name`` + ``description`` for the UI.
* The legal ``trigger_kind`` + ``action_kind`` + their default
  config payload. Operators override per-field at apply time
  (e.g. the channel id, role id, template string).
* Validation that the resolved config still satisfies the
  registry's ``required_config_keys``.

This PR ships **5 onboarding templates** (welcome, rules binding,
new-member role, delayed follow-up, notify-staff-on-join). Track 7
PR 21 adds channel-template presets, Track 7 PR 22 adds the
server-pulse presets — they extend the same template tuple.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from services.automation_registry import (
    KNOWN_ACTION_KINDS,
    KNOWN_TRIGGER_KINDS,
    UNSUPPORTED_INSTALLABLE_TRIGGER_KINDS,
    validate_action_config,
    validate_trigger_config,
)

logger = logging.getLogger("bot.services.automation_templates")


@dataclass(frozen=True)
class AutomationTemplate:
    """One preset that maps to a single ``automation_rules`` row."""

    slug: str
    display_name: str
    description: str
    trigger_kind: str
    action_kind: str
    default_trigger_config: dict[str, Any] = field(default_factory=dict)
    default_action_config: dict[str, Any] = field(default_factory=dict)
    required_overrides: tuple[str, ...] = ()
    category: str = "uncategorized"

    def merged_trigger_config(
        self,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        out = dict(self.default_trigger_config)
        if overrides:
            out.update(overrides)
        return out

    def merged_action_config(
        self,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        out = dict(self.default_action_config)
        if overrides:
            out.update(overrides)
        return out

    def validate(
        self,
        *,
        trigger_overrides: dict[str, Any] | None = None,
        action_overrides: dict[str, Any] | None = None,
    ) -> list[str]:
        """Return validation errors after merging overrides.

        Empty list = the resolved config would survive
        ``automation_registry`` validation.
        """
        errors: list[str] = []
        if self.trigger_kind not in KNOWN_TRIGGER_KINDS:
            errors.append(f"trigger_kind {self.trigger_kind!r} not in registry")
        if self.action_kind not in KNOWN_ACTION_KINDS:
            errors.append(f"action_kind {self.action_kind!r} not in registry")
        if errors:
            return errors
        trigger_cfg = self.merged_trigger_config(trigger_overrides)
        action_cfg = self.merged_action_config(action_overrides)
        errors.extend(validate_trigger_config(self.trigger_kind, trigger_cfg))
        errors.extend(validate_action_config(self.action_kind, action_cfg))
        # The template-level required_overrides catches "operator must
        # pick a channel" / "operator must pick a role" gaps that the
        # default config left blank as a placeholder (e.g. channel_id=0).
        for key in self.required_overrides:
            if not _has_meaningful_override(
                key,
                trigger_overrides,
                action_overrides,
            ):
                errors.append(
                    f"template {self.slug!r} requires override for {key!r}",
                )
        return errors


def _has_meaningful_override(
    key: str,
    trigger_overrides: dict[str, Any] | None,
    action_overrides: dict[str, Any] | None,
) -> bool:
    for overrides in (trigger_overrides, action_overrides):
        if overrides and key in overrides:
            value = overrides[key]
            if value not in (None, 0, ""):
                return True
    return False


# ---------------------------------------------------------------------------
# Onboarding templates (Track 7 PR 19)
# ---------------------------------------------------------------------------


_ONBOARDING_TEMPLATES: tuple[AutomationTemplate, ...] = (
    AutomationTemplate(
        slug="welcome-message",
        display_name="Welcome message",
        description=(
            "Send a configurable welcome message to a specific "
            "channel whenever a new member joins."
        ),
        trigger_kind="member_join",
        action_kind="send_message",
        default_action_config={
            "channel_id": 0,
            "template": "Welcome, {{member}}! 👋",
        },
        required_overrides=("channel_id",),
        category="onboarding",
    ),
    AutomationTemplate(
        slug="rules-channel-binding",
        display_name="Bind rules channel",
        description=(
            "Bind the operator-selected channel as the rules channel "
            "so the wizard and the launcher both know where to point "
            "new members."
        ),
        trigger_kind="manual",
        action_kind="bind_channel",
        default_action_config={
            "subsystem": "logging",
            "binding_name": "rules_channel",
            "channel_id": 0,
        },
        required_overrides=("channel_id",),
        category="onboarding",
    ),
    AutomationTemplate(
        slug="new-member-role",
        display_name="New member role",
        description=(
            "Assign the configured role to anyone who joins the guild. "
            "Operator picks the role id."
        ),
        trigger_kind="member_join",
        action_kind="assign_role",
        default_action_config={"role_id": 0},
        required_overrides=("role_id",),
        category="onboarding",
    ),
    AutomationTemplate(
        slug="delayed-followup-message",
        display_name="Delayed follow-up message",
        description=(
            "After a recurring interval, DM the guild owner with a "
            "check-in reminder. Useful for nudging the operator to "
            "re-run readiness."
        ),
        trigger_kind="interval",
        action_kind="notify_owner",
        default_trigger_config={"interval_minutes": 10080},  # 1 week
        default_action_config={
            "template": ("Reminder: run /setup to refresh readiness."),
        },
        category="onboarding",
    ),
    AutomationTemplate(
        slug="notify-staff-on-join",
        display_name="Notify staff on join",
        description=(
            "Post a notice to the configured staff channel whenever a new member joins."
        ),
        trigger_kind="member_join",
        action_kind="send_message",
        default_action_config={
            "channel_id": 0,
            "template": "🆕 {{member}} joined the server.",
        },
        required_overrides=("channel_id",),
        category="onboarding",
    ),
)


# ---------------------------------------------------------------------------
# Server-pulse templates (Track 7 PR 22)
# ---------------------------------------------------------------------------
# Recurring rules the wizard offers under "Server pulse". All default
# disabled so the operator opts in explicitly.

_SERVER_PULSE_TEMPLATES: tuple[AutomationTemplate, ...] = (
    AutomationTemplate(
        slug="daily-readiness-reminder",
        display_name="Daily readiness reminder",
        description=(
            "Post the readiness embed to the configured channel every "
            "day so configuration drift stays visible."
        ),
        trigger_kind="scheduled_time",
        action_kind="post_readiness_summary",
        default_trigger_config={"quiet_hours": [22, 6]},
        default_action_config={"channel_id": 0},
        required_overrides=("channel_id",),
        category="server_pulse",
    ),
    AutomationTemplate(
        slug="weekly-server-health-summary",
        display_name="Weekly server health summary",
        description="Post the readiness embed weekly to a configured channel.",
        trigger_kind="interval",
        action_kind="post_readiness_summary",
        default_trigger_config={"interval_minutes": 10080},  # 7 days
        default_action_config={"channel_id": 0},
        required_overrides=("channel_id",),
        category="server_pulse",
    ),
    AutomationTemplate(
        slug="weekly-leaderboard",
        display_name="Weekly leaderboard",
        description=(
            "Post the leaderboard for a chosen subsystem to a channel every week."
        ),
        trigger_kind="interval",
        action_kind="post_leaderboard_summary",
        default_trigger_config={"interval_minutes": 10080},
        default_action_config={"channel_id": 0, "subsystem": "xp"},
        required_overrides=("channel_id",),
        category="server_pulse",
    ),
    AutomationTemplate(
        slug="daily-game-prompt",
        display_name="Daily game prompt",
        description=(
            "Send a message inviting members to play a game in the configured channel."
        ),
        trigger_kind="scheduled_time",
        action_kind="send_message",
        default_action_config={
            "channel_id": 0,
            "template": "🎲 Daily game time — drop into the games channel!",
        },
        required_overrides=("channel_id",),
        category="server_pulse",
    ),
    AutomationTemplate(
        slug="inactive-channel-nudge",
        display_name="Inactive channel nudge",
        description=(
            "Post a gentle nudge to a channel that has been quiet for more than N days."
        ),
        trigger_kind="channel_inactive",
        action_kind="send_message",
        default_trigger_config={"channel_id": 0, "days": 30},
        default_action_config={
            "channel_id": 0,
            "template": "🌱 This channel has been quiet — anyone around?",
        },
        required_overrides=("channel_id",),
        category="server_pulse",
    ),
    AutomationTemplate(
        slug="moderation-digest",
        display_name="Moderation digest",
        description="Send a weekly moderation summary to the staff channel.",
        trigger_kind="interval",
        action_kind="send_message",
        default_trigger_config={"interval_minutes": 10080},
        default_action_config={
            "channel_id": 0,
            "template": "🛡 Weekly moderation digest.",
        },
        required_overrides=("channel_id",),
        category="server_pulse",
    ),
    AutomationTemplate(
        slug="economy-summary",
        display_name="Economy summary",
        description="Post the economy leaderboard / shop summary weekly.",
        trigger_kind="interval",
        action_kind="post_leaderboard_summary",
        default_trigger_config={"interval_minutes": 10080},
        default_action_config={"channel_id": 0, "subsystem": "economy"},
        required_overrides=("channel_id",),
        category="server_pulse",
    ),
    AutomationTemplate(
        slug="tournament-reminder",
        display_name="Tournament reminder",
        description=(
            "Send a configurable reminder about the next tournament to "
            "a chosen channel."
        ),
        trigger_kind="scheduled_time",
        action_kind="send_message",
        default_action_config={
            "channel_id": 0,
            "template": "🏆 Tournament starting soon — sign up!",
        },
        required_overrides=("channel_id",),
        category="server_pulse",
    ),
    AutomationTemplate(
        slug="bot-update-changelog-post",
        display_name="Bot update / changelog post",
        description=(
            "Post a changelog message to the configured staff channel — "
            "useful for surfacing bot releases."
        ),
        trigger_kind="manual",
        action_kind="send_message",
        default_action_config={
            "channel_id": 0,
            "template": "🆕 SuperBot update — see #releases.",
        },
        required_overrides=("channel_id",),
        category="server_pulse",
    ),
)


_ALL_TEMPLATES: tuple[AutomationTemplate, ...] = (
    _ONBOARDING_TEMPLATES + _SERVER_PULSE_TEMPLATES
)


def is_installable_template(template: AutomationTemplate) -> bool:
    """Return True if the template's trigger kind is currently installable.

    Templates whose trigger kind lands in
    :data:`services.automation_registry.UNSUPPORTED_INSTALLABLE_TRIGGER_KINDS`
    stay in :data:`_ALL_TEMPLATES` (so :func:`get_template` and the
    future cron-parser PR can still find them) but are hidden from the
    operator picker. Re-enabling them is a one-line change in the
    registry once the underlying scheduler support ships.
    """
    return template.trigger_kind not in UNSUPPORTED_INSTALLABLE_TRIGGER_KINDS


TEMPLATES: tuple[AutomationTemplate, ...] = tuple(
    t for t in _ALL_TEMPLATES if is_installable_template(t)
)


# ---------------------------------------------------------------------------
# Server presets (Track 7 PR 21)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PresetOperation:
    """One step of a :class:`ServerPreset`.

    Operations stay in this leaf-level shape rather than reaching
    into pipeline APIs directly so the wizard can preview the full
    plan without touching Discord. ``kind`` literals:

    * ``"bind_channel"``  — operator selects an existing channel.
    * ``"create_channel"`` — provisioning pipeline creates it.
    * ``"create_role"``   — wizard creates the role (Track 8).
    * ``"add_rule"``      — apply an :class:`AutomationTemplate` by
                            slug with operator-supplied overrides.
    * ``"set_setting"``   — settings_mutation pipeline.
    * ``"set_binding_target"`` — binding_mutation pipeline against
                            an already-bound channel/role.
    """

    kind: str
    description: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServerPreset:
    """One named bundle of operations the wizard can apply at once."""

    slug: str
    display_name: str
    description: str
    operations: tuple[PresetOperation, ...] = ()
    suggested_role_names: tuple[str, ...] = ()
    suggested_categories: tuple[str, ...] = ()
    suggested_log_channels: tuple[str, ...] = ()
    suggested_command_channels: tuple[str, ...] = ()

    def operations_of_kind(self, kind: str) -> tuple[PresetOperation, ...]:
        return tuple(op for op in self.operations if op.kind == kind)


@dataclass(frozen=True)
class ReuseCandidate:
    """One operator-visible suggestion: 'reuse this existing channel
    instead of creating a new one'.
    """

    operation_index: int
    suggested_name: str
    existing_channel_id: int | None = None
    existing_role_id: int | None = None
    reason: str = ""


@dataclass(frozen=True)
class PresetPreview:
    """What :func:`apply_preset` would do.

    Pure read; tests pin that constructing this never touches the
    Discord API or the DB.
    """

    preset_slug: str
    operations: tuple[PresetOperation, ...] = ()
    reuse_candidates: tuple[ReuseCandidate, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def operation_count(self) -> int:
        return len(self.operations)


_SERVER_PRESETS: tuple[ServerPreset, ...] = (
    ServerPreset(
        slug="minimal",
        display_name="Minimal",
        description=(
            "Bare-bones setup: a rules channel binding + a mod log channel "
            "binding. Nothing else."
        ),
        suggested_log_channels=("bot-mod-log",),
        operations=(
            PresetOperation(
                kind="bind_channel",
                description="Bind the rules channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "rules_channel",
                },
            ),
            PresetOperation(
                kind="bind_channel",
                description="Bind the moderation log channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "mod_channel",
                },
            ),
        ),
    ),
    ServerPreset(
        slug="community",
        display_name="Community",
        description=(
            "Welcome flow + general / off-topic channel bindings + "
            "moderation log + new-member role."
        ),
        suggested_categories=("Community",),
        suggested_log_channels=("bot-mod-log",),
        suggested_command_channels=("bot-commands",),
        suggested_role_names=("New Member",),
        operations=(
            PresetOperation(
                kind="bind_channel",
                description="Bind the welcome channel.",
                payload={
                    "subsystem": "onboarding",
                    "binding_name": "welcome_channel",
                },
            ),
            PresetOperation(
                kind="bind_channel",
                description="Bind the rules channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "rules_channel",
                },
            ),
            PresetOperation(
                kind="bind_channel",
                description="Bind the moderation log channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "mod_channel",
                },
            ),
            PresetOperation(
                kind="add_rule",
                description="Welcome message on member join.",
                payload={"template_slug": "welcome-message"},
            ),
            PresetOperation(
                kind="add_rule",
                description="Auto-assign New Member role on join.",
                payload={"template_slug": "new-member-role"},
            ),
        ),
    ),
    ServerPreset(
        slug="gaming",
        display_name="Gaming",
        description=(
            "Community preset plus a games / leaderboard hub channel binding."
        ),
        suggested_categories=("Games",),
        suggested_log_channels=("bot-mod-log",),
        suggested_command_channels=("bot-commands",),
        operations=(
            PresetOperation(
                kind="bind_channel",
                description="Bind the rules channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "rules_channel",
                },
            ),
            PresetOperation(
                kind="bind_channel",
                description="Bind the moderation log channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "mod_channel",
                },
            ),
            PresetOperation(
                kind="bind_channel",
                description="Bind the leaderboard / counting channel.",
                payload={
                    "subsystem": "counting",
                    "binding_name": "channel",
                },
            ),
            PresetOperation(
                kind="add_rule",
                description="Notify staff when a new member joins.",
                payload={"template_slug": "notify-staff-on-join"},
            ),
        ),
    ),
    ServerPreset(
        slug="moderation-heavy",
        display_name="Moderation heavy",
        description=(
            "Strict log routing: mod / cleanup / audit channels each "
            "bound to dedicated channels."
        ),
        suggested_categories=("Moderation",),
        suggested_log_channels=("bot-mod-log", "bot-cleanup-log", "bot-audit-log"),
        operations=(
            PresetOperation(
                kind="bind_channel",
                description="Bind the rules channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "rules_channel",
                },
            ),
            PresetOperation(
                kind="bind_channel",
                description="Bind the moderation log channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "mod_channel",
                },
            ),
            PresetOperation(
                kind="bind_channel",
                description="Bind the cleanup log channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "cleanup_channel",
                },
            ),
            PresetOperation(
                kind="bind_channel",
                description="Bind the audit log channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "audit_channel",
                },
            ),
            PresetOperation(
                kind="set_setting",
                description="Turn logging on.",
                payload={
                    "subsystem": "logging",
                    "name": "enabled",
                    "value": True,
                },
            ),
        ),
    ),
    ServerPreset(
        slug="economy",
        display_name="Economy",
        description=("Bind economy + shop channels and seed the welcome message."),
        suggested_categories=("Economy",),
        operations=(
            PresetOperation(
                kind="bind_channel",
                description="Bind the economy announce channel.",
                payload={
                    "subsystem": "economy",
                    "binding_name": "announce_channel",
                },
            ),
            PresetOperation(
                kind="bind_channel",
                description="Bind the moderation log channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "mod_channel",
                },
            ),
            PresetOperation(
                kind="add_rule",
                description="Welcome message on member join.",
                payload={"template_slug": "welcome-message"},
            ),
        ),
    ),
    ServerPreset(
        slug="existing-safe",
        display_name="Existing-server safe",
        description=(
            "Binds likely-existing channels for rules + moderation log. "
            "Never creates channels, roles, or automation rules — safe to "
            "apply to a server that already has its own structure."
        ),
        suggested_log_channels=("bot-mod-log",),
        suggested_command_channels=("bot-commands",),
        operations=(
            PresetOperation(
                kind="bind_channel",
                description="Bind an existing rules channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "rules_channel",
                },
            ),
            PresetOperation(
                kind="bind_channel",
                description="Bind an existing moderation log channel.",
                payload={
                    "subsystem": "logging",
                    "binding_name": "mod_channel",
                },
            ),
            PresetOperation(
                kind="bind_channel",
                description="Bind an existing bot-commands channel.",
                payload={
                    "subsystem": "moderation",
                    "binding_name": "bot_command_channel",
                },
            ),
        ),
    ),
    ServerPreset(
        slug="custom",
        display_name="Custom",
        description=(
            "Empty preset — the wizard builds the operations list as the "
            "operator picks each binding."
        ),
        operations=(),
    ),
)


SERVER_PRESETS: tuple[ServerPreset, ...] = _SERVER_PRESETS


def known_preset_slugs() -> frozenset[str]:
    return frozenset(p.slug for p in SERVER_PRESETS)


def get_preset(slug: str) -> ServerPreset | None:
    for preset in SERVER_PRESETS:
        if preset.slug == slug:
            return preset
    return None


def preview_preset(
    preset: ServerPreset,
    *,
    existing_channels: dict[str, int] | None = None,
    existing_roles: dict[str, int] | None = None,
) -> PresetPreview:
    """Render the preset against the operator's current resources.

    Pure read — no Discord API, no DB. Returns the planned
    operations alongside reuse candidates: when ``existing_channels``
    or ``existing_roles`` contain a name that matches a suggested
    resource, surface it so the wizard can offer "reuse" instead of
    "create".
    """
    existing_channels = existing_channels or {}
    existing_roles = existing_roles or {}
    reuse: list[ReuseCandidate] = []
    warnings: list[str] = []

    for index, op in enumerate(preset.operations):
        if op.kind == "create_channel":
            name = str(op.payload.get("name") or "")
            channel_id = existing_channels.get(name.lower())
            if channel_id is not None:
                reuse.append(
                    ReuseCandidate(
                        operation_index=index,
                        suggested_name=name,
                        existing_channel_id=channel_id,
                        reason=f"channel #{name} already exists; reuse it.",
                    ),
                )
        elif op.kind == "create_role":
            name = str(op.payload.get("name") or "")
            role_id = existing_roles.get(name.lower())
            if role_id is not None:
                reuse.append(
                    ReuseCandidate(
                        operation_index=index,
                        suggested_name=name,
                        existing_role_id=role_id,
                        reason=f"role @{name} already exists; reuse it.",
                    ),
                )

    # Sanity warnings: every "add_rule" must reference a known
    # template slug.
    for index, op in enumerate(preset.operations):
        if op.kind == "add_rule":
            slug = str(op.payload.get("template_slug") or "")
            if get_template(slug) is None:
                warnings.append(
                    f"operation[{index}]: unknown template slug {slug!r}",
                )

    return PresetPreview(
        preset_slug=preset.slug,
        operations=preset.operations,
        reuse_candidates=tuple(reuse),
        warnings=tuple(warnings),
    )


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


def get_template(slug: str) -> AutomationTemplate | None:
    # Searches the full source catalog so internal callers (preset
    # preview, tests) can still resolve hidden templates by slug. The
    # operator-facing picker lists :data:`TEMPLATES` which is filtered
    # via :func:`is_installable_template`.
    for tmpl in _ALL_TEMPLATES:
        if tmpl.slug == slug:
            return tmpl
    return None


def list_templates_by_category(category: str) -> tuple[AutomationTemplate, ...]:
    return tuple(t for t in TEMPLATES if t.category == category)


def known_slugs() -> frozenset[str]:
    return frozenset(t.slug for t in TEMPLATES)


__all__ = [
    "SERVER_PRESETS",
    "TEMPLATES",
    "AutomationTemplate",
    "PresetOperation",
    "PresetPreview",
    "ReuseCandidate",
    "ServerPreset",
    "get_preset",
    "get_template",
    "is_installable_template",
    "known_preset_slugs",
    "known_slugs",
    "list_templates_by_category",
    "preview_preset",
]
