"""Tests for the deterministic role-template catalogue (server-management PR13).

Pins:

* every built-in template validates (names/colours/tiers within bounds, no
  duplicate names);
* the suggestion model structurally carries **no permissions field**;
* colour parsing is fail-safe;
* ``plan_template`` partitions create vs. already-exists purely (no I/O) and
  warns when the bot can't manage roles;
* ``suggestion_to_spec`` is JSON-serialisable and round-trips the role spec.
"""

from __future__ import annotations

import dataclasses
import json

import discord

from services import setup_role_templates as rt

# ---------------------------------------------------------------------------
# Catalogue integrity
# ---------------------------------------------------------------------------


def test_catalogue_is_non_empty():
    assert rt.list_templates(), "expected at least one built-in template"


def test_every_builtin_template_validates():
    for t in rt.list_templates():
        errors = rt.validate_template(t)
        assert errors == [], f"template {t.slug!r} invalid: {errors}"


def test_template_slugs_unique():
    slugs = [t.slug for t in rt.list_templates()]
    assert len(slugs) == len(set(slugs)), f"duplicate template slugs: {slugs}"


def test_get_template_and_known_slugs_agree():
    for slug in rt.known_template_slugs():
        assert rt.get_template(slug) is not None
    assert rt.get_template("does-not-exist") is None


def test_progression_templates_carry_tiers():
    time_t = rt.get_template("time-progression")
    xp_t = rt.get_template("xp-progression")
    assert time_t is not None and xp_t is not None
    assert all(s.time_days for s in time_t.suggestions)
    assert all(s.xp_level for s in xp_t.suggestions)


# ---------------------------------------------------------------------------
# Safety: no permissions, ever
# ---------------------------------------------------------------------------


def test_suggestion_model_has_no_permissions_field():
    names = {f.name for f in dataclasses.fields(rt.RoleSuggestion)}
    assert "permissions" not in names
    assert "permission" not in names


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_validate_suggestion_accepts_a_good_role():
    s = rt.RoleSuggestion("Veteran", "A label", "#5865F2", hoist=True, time_days=30)
    assert rt.validate_suggestion(s) == []


def test_validate_suggestion_rejects_bad_values():
    assert rt.validate_suggestion(rt.RoleSuggestion("")) != []
    assert rt.validate_suggestion(rt.RoleSuggestion("x" * 200)) != []
    assert rt.validate_suggestion(rt.RoleSuggestion("@everyone")) != []
    assert rt.validate_suggestion(rt.RoleSuggestion("ok", color="not-a-color")) != []
    assert rt.validate_suggestion(rt.RoleSuggestion("ok", time_days=0)) != []
    assert rt.validate_suggestion(rt.RoleSuggestion("ok", time_days=99999)) != []
    assert rt.validate_suggestion(rt.RoleSuggestion("ok", xp_level=0)) != []
    assert rt.validate_suggestion(rt.RoleSuggestion("ok", xp_level=99999)) != []


def test_validate_template_flags_duplicate_names():
    t = rt.RoleTemplate(
        slug="dup",
        display_name="Dup",
        description="",
        category="x",
        suggestions=(rt.RoleSuggestion("A"), rt.RoleSuggestion("a")),
    )
    assert any("duplicate" in e for e in rt.validate_template(t))


def test_validate_template_flags_empty():
    t = rt.RoleTemplate(slug="empty", display_name="E", description="", category="x")
    assert rt.validate_template(t) != []


# ---------------------------------------------------------------------------
# Colour parsing
# ---------------------------------------------------------------------------


def test_parse_color_valid_hex():
    color = rt.parse_color("#5865F2")
    assert isinstance(color, discord.Color)
    assert color.value == 0x5865F2


def test_parse_color_fail_safe():
    assert rt.parse_color(None) is None
    assert rt.parse_color("") is None
    assert rt.parse_color("nonsense") is None


# ---------------------------------------------------------------------------
# Planning (pure)
# ---------------------------------------------------------------------------


def test_plan_partitions_create_vs_exists():
    template = rt.RoleTemplate(
        slug="t",
        display_name="T",
        description="",
        category="x",
        suggestions=(
            rt.RoleSuggestion("Owner"),
            rt.RoleSuggestion("Member"),
        ),
    )
    plan = rt.plan_template(template, existing_roles={"member": 42})
    assert plan.create_count == 1
    assert plan.exists_count == 1
    created = {p.suggestion.name for p in plan.to_create}
    assert created == {"Owner"}
    existing = plan.existing[0]
    assert existing.suggestion.name == "Member"
    assert existing.existing_role_id == 42


def test_plan_is_case_insensitive_on_existing_names():
    template = rt.RoleTemplate(
        slug="t",
        display_name="T",
        description="",
        category="x",
        suggestions=(rt.RoleSuggestion("Moderator"),),
    )
    plan = rt.plan_template(template, existing_roles={"MODERATOR": 7})
    assert plan.create_count == 0
    assert plan.exists_count == 1


def test_plan_warns_when_bot_cannot_manage_roles():
    template = rt.get_template("community-hierarchy")
    assert template is not None
    plan = rt.plan_template(template, existing_roles={}, bot_can_manage_roles=False)
    assert any("manage roles" in w.lower() for w in plan.warnings)


def test_plan_no_warning_when_bot_can_manage():
    template = rt.get_template("community-hierarchy")
    assert template is not None
    plan = rt.plan_template(template, existing_roles={}, bot_can_manage_roles=True)
    assert plan.warnings == ()


# ---------------------------------------------------------------------------
# Spec serialisation
# ---------------------------------------------------------------------------


def test_suggestion_to_spec_is_json_serialisable_and_complete():
    s = rt.RoleSuggestion("Veteran", "label", "#5865F2", hoist=True, time_days=30)
    spec = rt.suggestion_to_spec(s, template_slug="time-progression")
    # Round-trips through JSON unchanged (the draft store persists it as JSONB).
    assert json.loads(json.dumps(spec)) == spec
    assert spec["color"] == "#5865F2"
    assert spec["hoist"] is True
    assert spec["time_days"] == 30
    assert spec["template_slug"] == "time-progression"
    assert "permissions" not in spec
