"""Automation registry — Phase 9g / Track 6 PR 15.

Typed metadata for the trigger and action kinds the automation
substrate knows about. The registry is what the
:mod:`utils.db.automation` write primitives and the mutation
pipeline (Track 6 PR 16) validate ``trigger_config`` /
``action_config`` payloads against.

Adding a new kind = adding a row here PLUS updating the SQL
``CHECK`` constraint in migration 032. An alignment test asserts
both sets stay in lock-step.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("bot.services.automation_registry")


@dataclass(frozen=True)
class TriggerSpec:
    """Metadata for one ``trigger_kind`` literal."""

    kind: str
    display_name: str
    description: str
    required_config_keys: tuple[str, ...] = ()
    optional_config_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActionSpec:
    """Metadata for one ``action_kind`` literal."""

    kind: str
    display_name: str
    description: str
    required_config_keys: tuple[str, ...] = ()
    optional_config_keys: tuple[str, ...] = ()
    requires_owner: bool = False


# ---------------------------------------------------------------------------
# Triggers (mirrors migration 032 CHECK)
# ---------------------------------------------------------------------------

TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec(
        kind="scheduled_time",
        display_name="Scheduled time",
        description=(
            "Fires at a fixed time according to ``schedule`` (cron-like) "
            "interpreted in the rule's ``timezone``."
        ),
        required_config_keys=(),
        optional_config_keys=("quiet_hours",),
    ),
    TriggerSpec(
        kind="interval",
        display_name="Recurring interval",
        description=(
            "Fires every N minutes. ``trigger_config['interval_minutes']`` is required."
        ),
        required_config_keys=("interval_minutes",),
        optional_config_keys=("quiet_hours",),
    ),
    TriggerSpec(
        kind="member_join",
        display_name="On member join",
        description=(
            "Fires from ``on_member_join``. No required config; the "
            "joining member is passed to the action."
        ),
    ),
    TriggerSpec(
        kind="setup_readiness_below",
        display_name="Setup readiness below threshold",
        description=(
            "Fires when the readiness score drops below "
            "``trigger_config['threshold']``."
        ),
        required_config_keys=("threshold",),
    ),
    TriggerSpec(
        kind="binding_missing",
        display_name="Binding missing",
        description=(
            "Fires when a specific binding goes ``missing`` or "
            "``stale``. ``trigger_config['subsystem']`` and "
            "``trigger_config['binding_name']`` are required."
        ),
        required_config_keys=("subsystem", "binding_name"),
    ),
    TriggerSpec(
        kind="channel_inactive",
        display_name="Channel inactive",
        description=(
            "Fires when a watched channel has been idle for "
            "``trigger_config['days']`` days."
        ),
        required_config_keys=("channel_id", "days"),
    ),
    TriggerSpec(
        kind="manual",
        display_name="Manual",
        description="Fires only via ``!automation run <name>``.",
    ),
)

KNOWN_TRIGGER_KINDS: frozenset[str] = frozenset(t.kind for t in TRIGGERS)

# Known at the schema/registry level, but temporarily blocked for new
# rule installation until cron parsing ships. ``automation_mutation``
# enforces the rejection at the service boundary; ``automation_templates``
# hides templates whose ``trigger_kind`` lands here from the operator
# picker but keeps them in the source catalog so the cron-parser PR can
# re-enable them by removing the kind from this set.
UNSUPPORTED_INSTALLABLE_TRIGGER_KINDS: frozenset[str] = frozenset({"scheduled_time"})


# ---------------------------------------------------------------------------
# Actions (mirrors migration 032 CHECK)
# ---------------------------------------------------------------------------

ACTIONS: tuple[ActionSpec, ...] = (
    ActionSpec(
        kind="send_message",
        display_name="Send message",
        description=(
            "Send a message to a target channel. "
            "``action_config['channel_id']`` and ``['template']`` "
            "are required."
        ),
        required_config_keys=("channel_id", "template"),
    ),
    ActionSpec(
        kind="assign_role",
        display_name="Assign role",
        description=(
            "Give a role to the trigger's target member. "
            "``action_config['role_id']`` is required."
        ),
        required_config_keys=("role_id",),
    ),
    ActionSpec(
        kind="remove_role",
        display_name="Remove role",
        description=(
            "Strip a role from the trigger's target member. "
            "``action_config['role_id']`` is required."
        ),
        required_config_keys=("role_id",),
    ),
    ActionSpec(
        kind="post_readiness_summary",
        display_name="Post readiness summary",
        description=("Render ``build_setup_readiness_embed`` to a channel."),
        required_config_keys=("channel_id",),
    ),
    ActionSpec(
        kind="post_leaderboard_summary",
        display_name="Post leaderboard summary",
        description=("Render the leaderboard for the configured subsystem."),
        required_config_keys=("channel_id", "subsystem"),
    ),
    ActionSpec(
        kind="bind_channel",
        display_name="Bind a channel",
        description=(
            "Wrap ``services.binding_mutation.BindingMutationPipeline."
            "set_binding`` for an existing channel."
        ),
        required_config_keys=("subsystem", "binding_name", "channel_id"),
        requires_owner=True,
    ),
    ActionSpec(
        kind="create_channel",
        display_name="Create a channel",
        description=(
            "Wrap "
            "``services.resource_provisioning.ResourceProvisioningPipeline."
            "provision`` for a new channel."
        ),
        required_config_keys=("subsystem", "binding_name", "name"),
        requires_owner=True,
    ),
    ActionSpec(
        kind="notify_owner",
        display_name="Notify guild owner",
        description=("DM the guild owner with a templated message."),
        required_config_keys=("template",),
    ),
)

KNOWN_ACTION_KINDS: frozenset[str] = frozenset(a.kind for a in ACTIONS)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


def get_trigger(kind: str) -> TriggerSpec | None:
    for spec in TRIGGERS:
        if spec.kind == kind:
            return spec
    return None


def get_action(kind: str) -> ActionSpec | None:
    for spec in ACTIONS:
        if spec.kind == kind:
            return spec
    return None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_trigger_config(
    kind: str,
    config: dict[str, Any],
) -> list[str]:
    """Return a list of validation errors. Empty list = valid."""
    spec = get_trigger(kind)
    if spec is None:
        return [f"unknown trigger_kind {kind!r}"]
    return _missing_keys(spec.required_config_keys, config, "trigger_config")


def validate_action_config(
    kind: str,
    config: dict[str, Any],
) -> list[str]:
    """Return a list of validation errors. Empty list = valid."""
    spec = get_action(kind)
    if spec is None:
        return [f"unknown action_kind {kind!r}"]
    return _missing_keys(spec.required_config_keys, config, "action_config")


def _missing_keys(
    required: tuple[str, ...],
    config: dict[str, Any],
    label: str,
) -> list[str]:
    errors: list[str] = []
    for key in required:
        if key not in config:
            errors.append(f"{label}: missing required key {key!r}")
    return errors


__all__ = [
    "ACTIONS",
    "KNOWN_ACTION_KINDS",
    "KNOWN_TRIGGER_KINDS",
    "TRIGGERS",
    "UNSUPPORTED_INSTALLABLE_TRIGGER_KINDS",
    "ActionSpec",
    "TriggerSpec",
    "get_action",
    "get_trigger",
    "validate_action_config",
    "validate_trigger_config",
]
