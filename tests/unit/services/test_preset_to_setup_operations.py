"""Tests for ``preset_operations_to_setup_operations`` adapter.

Pins:

* Each PresetOperation.kind maps to the right SetupOperation.kind.
* Every adapted op carries ``metadata.source = "preset:<slug>"``.
* Risk is escalated for create_role (high) and create_channel /
  add_rule (medium); bindings stay low.
* Every bundled SERVER_PRESET adapts cleanly without warnings.
* Unknown preset kinds adapt to a synthetic ``preset_unknown:<kind>``
  op so the dispatcher surfaces them rather than silently dropping.
"""

from __future__ import annotations

from services.automation_templates import (
    SERVER_PRESETS,
    PresetOperation,
)
from services.setup_operations import preset_operations_to_setup_operations


# ---------------------------------------------------------------------------
# Per-kind mapping
# ---------------------------------------------------------------------------


def test_bind_channel_adapter_preserves_subsystem_and_binding():
    preset_op = PresetOperation(
        kind="bind_channel",
        description="Bind the rules channel.",
        payload={"subsystem": "logging", "binding_name": "rules_channel"},
    )
    ops = preset_operations_to_setup_operations([preset_op], preset_slug="minimal")
    assert len(ops) == 1
    op = ops[0]
    assert op.kind == "bind_channel"
    assert op.subsystem == "logging"
    assert op.binding_name == "rules_channel"
    assert op.target_kind == "channel"


def test_create_channel_adapter_sets_resource_mode_create():
    preset_op = PresetOperation(
        kind="create_channel",
        description="Create #bot-mod-log.",
        payload={
            "subsystem": "logging",
            "binding_name": "mod_channel",
            "name": "bot-mod-log",
        },
    )
    ops = preset_operations_to_setup_operations([preset_op], preset_slug="community")
    assert len(ops) == 1
    op = ops[0]
    assert op.kind == "create_channel"
    assert op.subsystem == "logging"
    assert op.binding_name == "mod_channel"
    assert op.resource_name == "bot-mod-log"
    assert op.resource_mode == "create"


def test_create_role_adapter_uses_resource_name():
    preset_op = PresetOperation(
        kind="create_role",
        description="Create the New Member role.",
        payload={"name": "New Member"},
    )
    ops = preset_operations_to_setup_operations([preset_op], preset_slug="community")
    assert len(ops) == 1
    op = ops[0]
    assert op.kind == "create_role"
    assert op.resource_name == "New Member"
    assert op.resource_mode == "create"


def test_set_setting_adapter_passes_through_value():
    preset_op = PresetOperation(
        kind="set_setting",
        description="Enable logging.",
        payload={"subsystem": "logging", "setting_name": "enabled", "value": True},
    )
    ops = preset_operations_to_setup_operations([preset_op], preset_slug="moderation")
    assert ops[0].kind == "set_setting"
    assert ops[0].subsystem == "logging"
    assert ops[0].setting_name == "enabled"
    assert ops[0].value is True


def test_set_binding_target_adapter_maps_to_bind_channel_with_target_id():
    preset_op = PresetOperation(
        kind="set_binding_target",
        description="Bind to an existing channel by id.",
        payload={
            "subsystem": "logging",
            "binding_name": "mod_channel",
            "target_id": 999,
        },
    )
    ops = preset_operations_to_setup_operations([preset_op], preset_slug="minimal")
    assert ops[0].kind == "bind_channel"
    assert ops[0].target_id == 999


def test_add_rule_adapter_maps_to_add_automation_rule():
    preset_op = PresetOperation(
        kind="add_rule",
        description="Add the welcome message template.",
        payload={
            "template_slug": "welcome-message",
            "trigger_kind": "member_join",
            "action_kind": "post_message",
        },
    )
    ops = preset_operations_to_setup_operations([preset_op], preset_slug="community")
    op = ops[0]
    assert op.kind == "add_automation_rule"
    assert op.automation_rule_name == "welcome-message"
    assert op.trigger_kind == "member_join"
    assert op.action_kind == "post_message"


def test_unknown_kind_adapts_to_preset_unknown_marker():
    preset_op = PresetOperation(
        kind="weird_kind",
        description="?",
        payload={"subsystem": "x"},
    )
    ops = preset_operations_to_setup_operations([preset_op], preset_slug="test")
    assert ops[0].kind == "preset_unknown:weird_kind"
    # Subsystem still propagates so the dispatcher's not_yet_implemented
    # surface labels the row.
    assert ops[0].subsystem == "x"


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_metadata_source_uses_preset_slug():
    preset_op = PresetOperation(
        kind="bind_channel",
        description="Bind the rules channel.",
        payload={"subsystem": "logging", "binding_name": "rules_channel"},
    )
    ops = preset_operations_to_setup_operations([preset_op], preset_slug="community")
    assert ops[0].metadata["source"] == "preset:community"


def test_metadata_reason_uses_op_description_when_present():
    preset_op = PresetOperation(
        kind="bind_channel",
        description="Bind the rules channel.",
        payload={"subsystem": "logging", "binding_name": "rules_channel"},
    )
    ops = preset_operations_to_setup_operations([preset_op], preset_slug="x")
    assert "Bind the rules channel" in ops[0].metadata["reason"]


def test_metadata_risk_low_for_bindings_medium_for_create_channel():
    bind_op = PresetOperation(
        kind="bind_channel",
        description=".",
        payload={"subsystem": "logging", "binding_name": "rules_channel"},
    )
    create_ch_op = PresetOperation(
        kind="create_channel",
        description=".",
        payload={"name": "x", "subsystem": "logging"},
    )
    ops = preset_operations_to_setup_operations(
        [bind_op, create_ch_op], preset_slug="x",
    )
    assert ops[0].metadata["risk"] == "low"
    assert ops[1].metadata["risk"] == "medium"


def test_metadata_risk_high_for_create_role():
    role_op = PresetOperation(
        kind="create_role",
        description=".",
        payload={"name": "moderator"},
    )
    ops = preset_operations_to_setup_operations([role_op], preset_slug="x")
    assert ops[0].metadata["risk"] == "high"


def test_metadata_risk_medium_for_add_rule():
    rule_op = PresetOperation(
        kind="add_rule",
        description=".",
        payload={"template_slug": "welcome-message"},
    )
    ops = preset_operations_to_setup_operations([rule_op], preset_slug="x")
    assert ops[0].metadata["risk"] == "medium"


def test_metadata_confidence_high_for_preset_staged_ops():
    bind_op = PresetOperation(
        kind="bind_channel",
        description=".",
        payload={"subsystem": "logging", "binding_name": "rules_channel"},
    )
    ops = preset_operations_to_setup_operations([bind_op], preset_slug="x")
    assert ops[0].metadata["confidence"] == "high"


# ---------------------------------------------------------------------------
# End-to-end: every bundled preset adapts cleanly
# ---------------------------------------------------------------------------


def test_every_bundled_preset_adapts_without_dropping_ops():
    for preset in SERVER_PRESETS:
        ops = preset_operations_to_setup_operations(
            list(preset.operations),
            preset_slug=preset.slug,
        )
        assert len(ops) == len(preset.operations), (
            f"preset {preset.slug!r}: adapter dropped ops "
            f"({len(ops)} != {len(preset.operations)})"
        )
        # Every adapted op carries the preset source.
        for op in ops:
            assert op.metadata is not None
            assert op.metadata["source"] == f"preset:{preset.slug}"


def test_minimal_preset_produces_two_bind_channel_ops():
    minimal = next(p for p in SERVER_PRESETS if p.slug == "minimal")
    ops = preset_operations_to_setup_operations(
        list(minimal.operations),
        preset_slug="minimal",
    )
    assert all(op.kind == "bind_channel" for op in ops)
    assert {op.binding_name for op in ops} == {"rules_channel", "mod_channel"}
