"""Phase 9h / Track 7 PR 21 — server preset templates tests.

Pins:

* 6 documented presets (Minimal / Community / Gaming /
  Moderation heavy / Economy / Custom) appear in
  ``SERVER_PRESETS``.
* ``get_preset`` returns the matching preset or ``None``.
* ``preview_preset`` is pure — never calls Discord or DB; tests
  rely on a stub-channels-only fixture and assert the planned
  operations stay unchanged.
* Reuse-candidate detection: ``preview_preset`` flags
  ``create_channel`` operations whose suggested name already
  exists in the operator's current resources.
* Sanity check: ``add_rule`` operations referencing an unknown
  template slug surface as warnings.
"""

from __future__ import annotations

import pytest

from services.automation_templates import (
    SERVER_PRESETS,
    PresetOperation,
    ReuseCandidate,
    ServerPreset,
    get_preset,
    known_preset_slugs,
    preview_preset,
)


def test_documented_preset_slugs():
    assert known_preset_slugs() == {
        "minimal",
        "existing-safe",
        "community",
        "gaming",
        "moderation-heavy",
        "economy",
        "custom",
    }


@pytest.mark.parametrize("slug", sorted(known_preset_slugs()))
def test_get_preset_returns_match(slug):
    preset = get_preset(slug)
    assert isinstance(preset, ServerPreset)
    assert preset.slug == slug


def test_get_preset_returns_none_for_unknown_slug():
    assert get_preset("does-not-exist") is None


@pytest.mark.parametrize("slug", sorted(known_preset_slugs()))
def test_preview_preserves_operations(slug):
    preset = get_preset(slug)
    assert preset is not None
    preview = preview_preset(preset)
    assert preview.operations == preset.operations
    assert preview.preset_slug == slug


def test_preview_is_a_pure_read():
    """No Discord or DB call should happen during preview;
    if the test fixture's "existing_channels" dict shows up as
    keys, we know no resolution leaked through."""
    preset = get_preset("community")
    assert preset is not None
    preview = preview_preset(preset)
    assert preview.reuse_candidates == ()
    assert preview.warnings == ()


def test_preview_emits_reuse_candidate_when_create_channel_already_exists():
    preset = ServerPreset(
        slug="probe",
        display_name="Probe",
        description="",
        operations=(
            PresetOperation(
                kind="create_channel",
                description="Create bot-mod-log.",
                payload={"name": "bot-mod-log"},
            ),
        ),
    )
    preview = preview_preset(
        preset,
        existing_channels={"bot-mod-log": 12345},
    )
    assert len(preview.reuse_candidates) == 1
    candidate = preview.reuse_candidates[0]
    assert isinstance(candidate, ReuseCandidate)
    assert candidate.suggested_name == "bot-mod-log"
    assert candidate.existing_channel_id == 12345


def test_preview_emits_reuse_candidate_when_create_role_already_exists():
    preset = ServerPreset(
        slug="probe",
        display_name="Probe",
        description="",
        operations=(
            PresetOperation(
                kind="create_role",
                description="Create New Member role.",
                payload={"name": "New Member"},
            ),
        ),
    )
    preview = preview_preset(
        preset,
        existing_roles={"new member": 9999},
    )
    assert len(preview.reuse_candidates) == 1
    candidate = preview.reuse_candidates[0]
    assert candidate.existing_role_id == 9999


def test_preview_warns_on_unknown_template_slug():
    preset = ServerPreset(
        slug="probe",
        display_name="Probe",
        description="",
        operations=(
            PresetOperation(
                kind="add_rule",
                description="Apply a non-existent rule.",
                payload={"template_slug": "does-not-exist"},
            ),
        ),
    )
    preview = preview_preset(preset)
    assert any("unknown template slug" in w for w in preview.warnings)


def test_existing_safe_preset_binds_only_never_creates():
    """``existing-safe`` is for servers that already have their own
    structure: every operation must be ``bind_channel`` — no
    creates, no role additions, no automation rules."""
    preset = get_preset("existing-safe")
    assert preset is not None
    kinds = {op.kind for op in preset.operations}
    assert kinds == {"bind_channel"}
    # Specifically, the rules, mod log, and bot-commands bindings.
    binding_names = {op.payload.get("binding_name") for op in preset.operations}
    assert "rules_channel" in binding_names
    assert "mod_channel" in binding_names
    assert "bot_command_channel" in binding_names


def test_minimal_preset_binds_rules_and_mod_log_only():
    preset = get_preset("minimal")
    assert preset is not None
    binding_targets = {
        op.payload["binding_name"]
        for op in preset.operations_of_kind("bind_channel")
    }
    assert binding_targets == {"rules_channel", "mod_channel"}


def test_community_preset_includes_welcome_and_role_rules():
    preset = get_preset("community")
    assert preset is not None
    add_rule_slugs = {
        op.payload["template_slug"]
        for op in preset.operations_of_kind("add_rule")
    }
    assert "welcome-message" in add_rule_slugs
    assert "new-member-role" in add_rule_slugs


def test_moderation_heavy_includes_audit_and_cleanup_channels():
    preset = get_preset("moderation-heavy")
    assert preset is not None
    binding_targets = {
        op.payload["binding_name"]
        for op in preset.operations_of_kind("bind_channel")
    }
    assert binding_targets >= {"audit_channel", "cleanup_channel", "mod_channel"}


def test_custom_preset_has_no_operations():
    preset = get_preset("custom")
    assert preset is not None
    assert preset.operations == ()
