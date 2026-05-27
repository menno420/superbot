"""Phase 9h / Track 7 PR 22 — server-pulse templates tests.

Pins:

* All 9 documented server-pulse templates appear in
  ``list_templates_by_category("server_pulse")``.
* Each template's resolved (default + overrides) config passes the
  registry's validation.
* Templates round-trip through ``AutomationMutationPipeline``
  (mocked) without raising.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.automation_mutation import (
    AutomationMutationPipeline,
    InvalidAutomationConfigError,
)
from services.automation_templates import (
    AutomationTemplate,
    get_template,
    is_installable_template,
    list_templates_by_category,
)

# Templates the operator picker should currently surface (every kind
# the scheduler supports for installation).
_INSTALLABLE_SERVER_PULSE_SLUGS = {
    "weekly-server-health-summary",
    "weekly-leaderboard",
    "inactive-channel-nudge",
    "moderation-digest",
    "economy-summary",
    "bot-update-changelog-post",
}
# Templates that live in the source catalog (so the cron-parser PR can
# re-enable them) but are blocked at the mutation-service boundary.
_NON_INSTALLABLE_SERVER_PULSE_SLUGS = {
    "daily-readiness-reminder",
    "daily-game-prompt",
    "tournament-reminder",
}
_SERVER_PULSE_SLUGS = (
    _INSTALLABLE_SERVER_PULSE_SLUGS | _NON_INSTALLABLE_SERVER_PULSE_SLUGS
)


def test_server_pulse_slug_set_matches_documented():
    # Picker-facing list only exposes installable templates.
    actual_listed = {t.slug for t in list_templates_by_category("server_pulse")}
    assert actual_listed == _INSTALLABLE_SERVER_PULSE_SLUGS
    # Full catalog still resolves every documented slug via get_template
    # so internal callers (preset preview, future re-enable) keep working.
    for slug in _SERVER_PULSE_SLUGS:
        assert get_template(slug) is not None, slug


@pytest.mark.parametrize("slug", sorted(_SERVER_PULSE_SLUGS))
def test_template_category_is_server_pulse(slug):
    tmpl = get_template(slug)
    assert isinstance(tmpl, AutomationTemplate)
    assert tmpl.category == "server_pulse"


@pytest.mark.parametrize("slug", sorted(_SERVER_PULSE_SLUGS))
def test_template_validates_with_meaningful_overrides(slug):
    tmpl = get_template(slug)
    assert tmpl is not None
    overrides = _meaningful_overrides(tmpl)
    errors = tmpl.validate(action_overrides=overrides)
    assert errors == [], errors


@pytest.mark.parametrize("slug", sorted(_SERVER_PULSE_SLUGS))
def test_template_requires_channel_override(slug):
    tmpl = get_template(slug)
    assert tmpl is not None
    # No overrides — every server-pulse template ships with
    # ``channel_id=0`` as the placeholder.
    errors = tmpl.validate()
    assert any("channel_id" in e for e in errors)


@pytest.mark.asyncio
@pytest.mark.parametrize("slug", sorted(_INSTALLABLE_SERVER_PULSE_SLUGS))
async def test_installable_template_round_trip_through_pipeline(slug):
    tmpl = get_template(slug)
    assert tmpl is not None
    assert is_installable_template(tmpl)
    action_cfg = tmpl.merged_action_config(_meaningful_overrides(tmpl))
    trigger_cfg = tmpl.merged_trigger_config()
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


@pytest.mark.asyncio
@pytest.mark.parametrize("slug", sorted(_NON_INSTALLABLE_SERVER_PULSE_SLUGS))
async def test_non_installable_template_is_rejected_by_pipeline(slug):
    tmpl = get_template(slug)
    assert tmpl is not None
    assert not is_installable_template(tmpl)
    action_cfg = tmpl.merged_action_config(_meaningful_overrides(tmpl))
    trigger_cfg = tmpl.merged_trigger_config()
    with (
        patch(
            "services.automation_mutation.db.insert_rule",
            new_callable=AsyncMock,
        ) as insert_rule,
        patch(
            "services.automation_mutation.emit_audit_action",
            new_callable=AsyncMock,
        ),
        patch("core.events.bus.emit", new_callable=AsyncMock),
    ):
        with pytest.raises(InvalidAutomationConfigError):
            await AutomationMutationPipeline().create_rule(
                guild_id=10,
                guild_owner_id=99,
                name=tmpl.slug,
                trigger_kind=tmpl.trigger_kind,
                action_kind=tmpl.action_kind,
                trigger_config=trigger_cfg,
                action_config=action_cfg,
                actor_id=99,
            )
        insert_rule.assert_not_awaited()


def test_all_server_pulse_templates_default_to_disabled():
    """The mutation pipeline always inserts ``enabled=False`` —
    operators opt in explicitly. The template definitions
    deliberately don't carry an ``enabled`` field so the default
    survives."""
    # Pin via structure across the full catalog: no template has an
    # "enabled" key in its default config — including the hidden
    # scheduled_time ones so a future re-enable doesn't accidentally
    # bypass the disabled-by-default invariant.
    for slug in _SERVER_PULSE_SLUGS:
        tmpl = get_template(slug)
        assert tmpl is not None
        assert "enabled" not in tmpl.default_trigger_config
        assert "enabled" not in tmpl.default_action_config


def _meaningful_overrides(tmpl):
    overrides = {}
    for key in tmpl.required_overrides:
        if key.endswith("_id"):
            overrides[key] = 4242
        elif key == "template":
            overrides[key] = "hello"
        else:
            overrides[key] = "x"
    return overrides
