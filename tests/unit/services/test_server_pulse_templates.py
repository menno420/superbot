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

from services.automation_mutation import AutomationMutationPipeline
from services.automation_templates import (
    AutomationTemplate,
    get_template,
    list_templates_by_category,
)

_SERVER_PULSE_SLUGS = {
    "daily-readiness-reminder",
    "weekly-server-health-summary",
    "weekly-leaderboard",
    "daily-game-prompt",
    "inactive-channel-nudge",
    "moderation-digest",
    "economy-summary",
    "tournament-reminder",
    "bot-update-changelog-post",
}


def test_server_pulse_slug_set_matches_documented():
    actual = {t.slug for t in list_templates_by_category("server_pulse")}
    assert actual == _SERVER_PULSE_SLUGS


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
@pytest.mark.parametrize("slug", sorted(_SERVER_PULSE_SLUGS))
async def test_template_round_trip_through_pipeline(slug):
    tmpl = get_template(slug)
    assert tmpl is not None
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


def test_all_server_pulse_templates_default_to_disabled():
    """The mutation pipeline always inserts ``enabled=False`` —
    operators opt in explicitly. The template definitions
    deliberately don't carry an ``enabled`` field so the default
    survives."""
    # Pin via structure: no template has an "enabled" key in its
    # default config.
    for tmpl in list_templates_by_category("server_pulse"):
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
