"""Phase 9h / Track 7 PR 19 — onboarding automation templates tests.

Pins:

* The 5 onboarding templates are present in ``TEMPLATES`` with
  the documented slugs.
* Each template's resolved (default + overrides) config passes
  the registry's required-key validation.
* ``required_overrides`` rejects empty / zero placeholders so the
  wizard surfaces "please pick a channel" instead of letting an
  invalid rule land.
* Templates round-trip through
  ``AutomationMutationPipeline.create_rule`` (mocked) without
  raising ``InvalidAutomationConfigError``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.automation_mutation import (
    AutomationMutationPipeline,
    InvalidAutomationConfigError,
)
from services.automation_templates import (
    SERVER_PRESETS,
    TEMPLATES,
    AutomationTemplate,
    get_template,
    is_installable_template,
    known_slugs,
    list_templates_by_category,
)

# ---------------------------------------------------------------------------
# Catalogue contents
# ---------------------------------------------------------------------------


def test_onboarding_slugs_match_documented_set():
    onboarding_slugs = {t.slug for t in list_templates_by_category("onboarding")}
    assert onboarding_slugs == {
        "welcome-message",
        "rules-channel-binding",
        "new-member-role",
        "delayed-followup-message",
        "notify-staff-on-join",
    }


def test_get_template_returns_match():
    tmpl = get_template("welcome-message")
    assert isinstance(tmpl, AutomationTemplate)
    assert tmpl.action_kind == "send_message"


def test_get_template_returns_none_for_unknown_slug():
    assert get_template("does-not-exist") is None


def test_get_template_can_still_find_hidden_unsupported_template():
    """Templates whose trigger kind isn't installable yet stay in the
    source catalog so internal callers (preset preview, future
    cron-parser PR) can still resolve them by slug. They're only
    hidden from the operator picker / ``TEMPLATES`` listing.
    """
    # ``daily-readiness-reminder`` ships with trigger_kind=scheduled_time.
    tmpl = get_template("daily-readiness-reminder")
    assert tmpl is not None
    assert not is_installable_template(tmpl)
    # Picker-facing listing excludes it.
    assert tmpl not in TEMPLATES
    assert tmpl.slug not in known_slugs()


def test_server_presets_do_not_reference_unsupported_templates():
    """Bundled :data:`SERVER_PRESETS` must not point any ``add_rule``
    operation at a non-installable template. Otherwise an operator
    applying the preset would get an ``InvalidAutomationConfigError``
    from the mutation pipeline mid-apply.
    """
    for preset in SERVER_PRESETS:
        for index, op in enumerate(preset.operations):
            if op.kind != "add_rule":
                continue
            slug = str(op.payload.get("template_slug") or "")
            tmpl = get_template(slug)
            assert tmpl is not None, (
                f"preset {preset.slug!r} operation[{index}] references "
                f"unknown template slug {slug!r}"
            )
            assert is_installable_template(tmpl), (
                f"preset {preset.slug!r} operation[{index}] references "
                f"non-installable template {slug!r} (trigger_kind="
                f"{tmpl.trigger_kind!r}); the apply would fail at the "
                "mutation-pipeline boundary."
            )


def test_list_templates_by_category_filters():
    items = list_templates_by_category("onboarding")
    onboarding_slugs = {
        "welcome-message",
        "rules-channel-binding",
        "new-member-role",
        "delayed-followup-message",
        "notify-staff-on-join",
    }
    assert {t.slug for t in items} == onboarding_slugs
    assert list_templates_by_category("uncategorized") == ()


# ---------------------------------------------------------------------------
# Per-template validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", sorted(known_slugs()))
def test_template_validates_with_meaningful_overrides(slug):
    tmpl = get_template(slug)
    assert tmpl is not None
    overrides = _meaningful_overrides_for(tmpl)
    errors = tmpl.validate(action_overrides=overrides)
    assert errors == [], errors


@pytest.mark.parametrize("slug", sorted(known_slugs()))
def test_template_rejects_missing_required_overrides(slug):
    tmpl = get_template(slug)
    assert tmpl is not None
    if not tmpl.required_overrides:
        pytest.skip("template has no required_overrides")
    # No overrides; the placeholder zero / empty values should fail
    # the template-level required-override check.
    errors = tmpl.validate()
    assert any("requires override" in e for e in errors), errors


def test_zero_value_does_not_satisfy_required_override():
    tmpl = get_template("welcome-message")
    assert tmpl is not None
    errors = tmpl.validate(action_overrides={"channel_id": 0})
    assert any("channel_id" in e for e in errors)


# ---------------------------------------------------------------------------
# Round-trip through the mutation pipeline (mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("slug", sorted(known_slugs()))
async def test_template_apply_round_trip_via_pipeline(slug):
    tmpl = get_template(slug)
    assert tmpl is not None
    trigger_cfg = tmpl.merged_trigger_config(
        _meaningful_overrides_for(tmpl, scope="trigger"),
    )
    action_cfg = tmpl.merged_action_config(
        _meaningful_overrides_for(tmpl, scope="action"),
    )

    with (
        patch(
            "services.automation_mutation.db.insert_rule",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.automation_mutation.emit_audit_action",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch("core.events.bus.emit", new_callable=AsyncMock),
    ):
        result = await AutomationMutationPipeline().create_rule(
            guild_id=10,
            guild_owner_id=99,
            name=tmpl.slug,
            trigger_kind=tmpl.trigger_kind,
            action_kind=tmpl.action_kind,
            trigger_config=trigger_cfg,
            action_config=action_cfg,
            actor_id=99,
        )
    assert result.rule_id == 1
    assert result.mutation_type == "create"


@pytest.mark.asyncio
async def test_template_apply_without_required_override_raises():
    tmpl = get_template("welcome-message")
    assert tmpl is not None
    with (
        patch(
            "services.automation_mutation.db.insert_rule",
            new_callable=AsyncMock,
        ),
        patch(
            "services.automation_mutation.emit_audit_action",
            new_callable=AsyncMock,
        ),
        patch("core.events.bus.emit", new_callable=AsyncMock),
    ):
        # Use the template's default channel_id=0 (placeholder), no
        # overrides — pipeline validation tolerates the missing
        # template field but the action_config still lacks
        # ``channel_id`` if we strip it. So pass a config that the
        # registry rejects: drop ``channel_id`` entirely.
        with pytest.raises(InvalidAutomationConfigError):
            await AutomationMutationPipeline().create_rule(
                guild_id=10,
                guild_owner_id=99,
                name=tmpl.slug,
                trigger_kind=tmpl.trigger_kind,
                action_kind=tmpl.action_kind,
                trigger_config=tmpl.merged_trigger_config(),
                action_config={"template": "x"},  # channel_id removed
                actor_id=99,
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _meaningful_overrides_for(
    tmpl: AutomationTemplate,
    *,
    scope: str = "action",
):
    """Return overrides that satisfy ``required_overrides`` with
    sensible non-zero values."""
    overrides: dict[str, object] = {}
    for key in tmpl.required_overrides:
        if key.endswith("_id"):
            overrides[key] = 4242
        elif key == "template":
            overrides[key] = "hello"
        else:
            overrides[key] = "x"
    if scope == "action":
        return overrides
    return {}
