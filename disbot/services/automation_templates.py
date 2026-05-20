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
            "Post a notice to the configured staff channel whenever a "
            "new member joins."
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


TEMPLATES: tuple[AutomationTemplate, ...] = _ONBOARDING_TEMPLATES


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


def get_template(slug: str) -> AutomationTemplate | None:
    for tmpl in TEMPLATES:
        if tmpl.slug == slug:
            return tmpl
    return None


def list_templates_by_category(category: str) -> tuple[AutomationTemplate, ...]:
    return tuple(t for t in TEMPLATES if t.category == category)


def known_slugs() -> frozenset[str]:
    return frozenset(t.slug for t in TEMPLATES)


__all__ = [
    "TEMPLATES",
    "AutomationTemplate",
    "get_template",
    "known_slugs",
    "list_templates_by_category",
]
