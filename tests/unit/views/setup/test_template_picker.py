"""PR-D — ``views.setup.template_picker`` tests.

Covers:

* Picker embed lists known categories.
* The select populates options from :data:`TEMPLATES`.
* :func:`apply_template_to_guild` routes through
  :class:`AutomationMutationPipeline.create_rule` with the right
  template defaults + override injection, and never sets
  ``enabled=True``.
* Apply with a missing required override is short-circuited with a
  validation message; the pipeline is not called.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.automation_mutation import AutomationMutationResult
from services.automation_templates import (
    TEMPLATES,
    AutomationTemplate,
    get_template,
)
from views.setup.template_picker import (
    ApplyOutcome,
    TemplateConfigView,
    TemplatePickerView,
    apply_template_to_guild,
    build_picker_embed,
    build_template_config_embed,
)


def _author():
    member = MagicMock()
    member.id = 99
    return member


def test_build_picker_embed_lists_categories_with_counts():
    embed = build_picker_embed()
    assert "Choose a preset" in embed.title
    fields = embed.fields
    cat_field = next((f for f in fields if "categories" in f.name.lower()), None)
    assert cat_field is not None
    # At least one of the documented categories appears.
    assert "Onboarding" in cat_field.value or "Server pulse" in cat_field.value


def test_picker_view_seeds_one_select_with_template_options():
    view = TemplatePickerView(_author())
    selects = [c for c in view.children if hasattr(c, "options")]
    assert len(selects) == 1
    select = selects[0]
    assert len(select.options) >= 1
    # First option should map to a known slug.
    first_slug = select.options[0].value
    assert get_template(first_slug) is not None


def test_template_config_embed_pre_apply_lists_required_overrides():
    template = next(t for t in TEMPLATES if t.required_overrides)
    embed = build_template_config_embed(template)
    field = next(f for f in embed.fields if "Required" in f.name)
    assert any(f"`{key}`" in field.value for key in template.required_overrides)


def test_template_config_embed_post_apply_success_is_green():
    template = next(iter(TEMPLATES))
    outcome = ApplyOutcome(
        ok=True,
        rule_id=42,
        template_slug=template.slug,
        detail="ok",
    )
    embed = build_template_config_embed(template, outcome=outcome)
    assert embed.color is not None
    assert "Installed" in embed.title
    assert "42" in embed.description


def test_template_config_embed_post_apply_failure_is_red():
    template = next(iter(TEMPLATES))
    outcome = ApplyOutcome(
        ok=False,
        rule_id=None,
        template_slug=template.slug,
        detail="something blew up",
    )
    embed = build_template_config_embed(template, outcome=outcome)
    assert "Could not install" in embed.title
    assert "something blew up" in embed.description


@pytest.mark.asyncio
async def test_apply_routes_through_mutation_pipeline_with_disabled_default():
    """Apply must call the pipeline and never pass ``enabled=True``."""
    template = next(t for t in TEMPLATES if "channel_id" in t.required_overrides)

    fake_result = AutomationMutationResult(
        mutation_id="m1",
        rule_id=101,
        guild_id=1,
        mutation_type="create",
        name=template.slug,
        trigger_kind=template.trigger_kind,
        action_kind=template.action_kind,
        prev_enabled=None,
        new_enabled=False,
        committed_at=None,  # type: ignore[arg-type]
        event_emitted=True,
    )

    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.create_rule = AsyncMock(return_value=fake_result)
    pipeline_class.return_value = pipeline_instance

    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        pipeline_class,
    ):
        outcome = await apply_template_to_guild(
            template=template,
            guild_id=1,
            guild_owner_id=99,
            channel_id=12345,
            role_id=None,
            actor_id=99,
        )

    assert outcome.ok is True
    assert outcome.rule_id == 101
    pipeline_instance.create_rule.assert_awaited_once()
    kwargs = pipeline_instance.create_rule.await_args.kwargs
    assert kwargs["guild_id"] == 1
    assert kwargs["actor_type"] == "platform_owner"
    assert kwargs["trigger_kind"] == template.trigger_kind
    assert kwargs["action_kind"] == template.action_kind
    # No `enabled` kwarg passed at all — pipeline defaults to false.
    assert "enabled" not in kwargs
    # The selected channel id must appear in either action or trigger config.
    action_config = kwargs.get("action_config", {})
    trigger_config = kwargs.get("trigger_config", {})
    assert (
        action_config.get("channel_id") == 12345
        or trigger_config.get("channel_id") == 12345
    )


@pytest.mark.asyncio
async def test_apply_returns_validation_error_when_pipeline_rejects():
    template = next(t for t in TEMPLATES if "channel_id" in t.required_overrides)

    from services.automation_mutation import InvalidAutomationConfigError

    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.create_rule = AsyncMock(
        side_effect=InvalidAutomationConfigError("channel_id is required"),
    )
    pipeline_class.return_value = pipeline_instance

    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        pipeline_class,
    ):
        outcome = await apply_template_to_guild(
            template=template,
            guild_id=1,
            guild_owner_id=99,
            channel_id=0,  # invalid sentinel
            role_id=None,
            actor_id=99,
        )

    assert outcome.ok is False
    assert "channel_id is required" in outcome.detail


@pytest.mark.asyncio
async def test_apply_button_short_circuits_when_required_override_missing():
    """Apply with required ``channel_id`` unset must not call the pipeline."""
    template = next(t for t in TEMPLATES if "channel_id" in t.required_overrides)
    view = TemplateConfigView(_author(), template=template)
    # channel_id was never selected.
    assert view.selected_channel_id is None

    interaction = MagicMock()
    interaction.guild = MagicMock(id=1, owner_id=99)
    interaction.user = MagicMock(id=99)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()

    with patch(
        "views.setup.template_picker.apply_template_to_guild",
        new_callable=AsyncMock,
    ) as apply_mock:
        await view._apply.callback(interaction)

    apply_mock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "channel_id" in msg


@pytest.mark.asyncio
async def test_apply_button_calls_pipeline_when_overrides_filled():
    template = next(t for t in TEMPLATES if "channel_id" in t.required_overrides)
    view = TemplateConfigView(_author(), template=template)
    view.selected_channel_id = 12345

    interaction = MagicMock()
    interaction.guild = MagicMock(id=1, owner_id=99)
    interaction.user = MagicMock(id=99)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()

    outcome = ApplyOutcome(
        ok=True,
        rule_id=42,
        template_slug=template.slug,
        detail="ok",
    )
    with patch(
        "views.setup.template_picker.apply_template_to_guild",
        new_callable=AsyncMock,
        return_value=outcome,
    ) as apply_mock:
        await view._apply.callback(interaction)

    apply_mock.assert_awaited_once()
    interaction.response.send_message.assert_awaited_once()
    kwargs = apply_mock.await_args.kwargs
    assert kwargs["template"].slug == template.slug
    assert kwargs["guild_id"] == 1
    assert kwargs["channel_id"] == 12345


def test_picker_select_options_never_exceed_25():
    view = TemplatePickerView(_author())
    selects = [c for c in view.children if hasattr(c, "options")]
    assert len(selects[0].options) <= 25


def test_picker_omits_unsupported_trigger_kinds():
    """Templates whose trigger kind isn't installable yet must not
    appear in the picker — operators would otherwise install a rule
    the scheduler treats as a 24h-drift placeholder.
    """
    from services.automation_registry import (
        UNSUPPORTED_INSTALLABLE_TRIGGER_KINDS,
    )

    view = TemplatePickerView(_author())
    select = next(c for c in view.children if hasattr(c, "options"))
    listed_slugs = {opt.value for opt in select.options}
    for slug in listed_slugs:
        tmpl = get_template(slug)
        assert tmpl is not None
        assert tmpl.trigger_kind not in UNSUPPORTED_INSTALLABLE_TRIGGER_KINDS
    # Belt-and-braces: TEMPLATES (the source of the options) carries no
    # unsupported kinds either.
    for tmpl in TEMPLATES:
        assert tmpl.trigger_kind not in UNSUPPORTED_INSTALLABLE_TRIGGER_KINDS
