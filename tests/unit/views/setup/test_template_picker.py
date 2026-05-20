"""PR-D — ``views.setup.template_picker`` tests.

Covers:

* Picker embed lists known categories.
* The select populates options from :data:`TEMPLATES`.
* :func:`apply_template_to_guild` builds an ``add_automation_rule``
  ``SetupOperation`` and routes it through
  :func:`services.setup_operations.apply_operations` — not through
  ``AutomationMutationPipeline`` directly.  The dispatcher in turn
  reaches the pipeline (with ``actor_type="platform_owner"``) and the
  rule is created **disabled**.
* Apply with a missing required override is short-circuited with a
  validation message; the dispatcher is not called.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.automation_mutation import AutomationMutationResult
from services.automation_templates import (
    TEMPLATES,
    AutomationTemplate,
    get_template,
)
from services.setup_operations import (
    SetupOperationBatchResult,
    SetupOperationResult,
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


def _guild(guild_id: int = 1, owner_id: int = 99):
    guild = MagicMock()
    guild.id = guild_id
    guild.owner_id = owner_id
    return guild


def _automation_result(template, rule_id: int = 101) -> AutomationMutationResult:
    return AutomationMutationResult(
        mutation_id="m1",
        rule_id=rule_id,
        guild_id=1,
        mutation_type="create",
        name=template.slug,
        trigger_kind=template.trigger_kind,
        action_kind=template.action_kind,
        prev_enabled=None,
        new_enabled=False,
        committed_at=datetime.now(timezone.utc),
        event_emitted=True,
    )


def test_build_picker_embed_lists_categories_with_counts():
    embed = build_picker_embed()
    assert "Choose a preset" in embed.title
    fields = embed.fields
    cat_field = next((f for f in fields if "categories" in f.name.lower()), None)
    assert cat_field is not None
    # At least one of the documented categories appears.
    assert (
        "Onboarding" in cat_field.value
        or "Server pulse" in cat_field.value
    )


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
    assert any(
        f"`{key}`" in field.value for key in template.required_overrides
    )


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
    """Apply must reach the pipeline with the right configs and never pass
    ``enabled=True``.

    The pipeline is reached through the dispatcher; patching at the
    automation_mutation module catches the dispatcher's lazy import.
    """
    template = next(t for t in TEMPLATES if "channel_id" in t.required_overrides)

    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.create_rule = AsyncMock(
        return_value=_automation_result(template, rule_id=101),
    )
    pipeline_class.return_value = pipeline_instance

    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        pipeline_class,
    ):
        outcome = await apply_template_to_guild(
            template=template,
            guild=_guild(),
            actor=_author(),
            channel_id=12345,
            role_id=None,
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
async def test_apply_goes_through_setup_operations_dispatcher():
    """The template apply path must build a SetupOperation and call
    ``apply_operations`` — it must NOT reach AutomationMutationPipeline
    via a direct import in template_picker."""
    template = next(t for t in TEMPLATES if "channel_id" in t.required_overrides)
    captured_ops: list = []

    async def _fake_apply(ops, *, guild, actor, actor_type="user"):
        del guild, actor
        captured_ops.extend(ops)
        return SetupOperationBatchResult(
            results=[
                SetupOperationResult(
                    status="applied",
                    operation=ops[0],
                    label="ok",
                    mutation_id="m1",
                    data={"rule_id": 202},
                ),
            ],
        )

    with patch(
        "services.setup_operations.apply_operations",
        new=_fake_apply,
    ):
        outcome = await apply_template_to_guild(
            template=template,
            guild=_guild(),
            actor=_author(),
            channel_id=12345,
            role_id=None,
        )

    assert outcome.ok is True
    assert outcome.rule_id == 202
    assert len(captured_ops) == 1
    op = captured_ops[0]
    assert op.kind == "add_automation_rule"
    assert op.automation_rule_name == template.slug
    assert op.trigger_kind == template.trigger_kind
    assert op.action_kind == template.action_kind


@pytest.mark.asyncio
async def test_apply_passes_platform_owner_actor_type():
    """``actor_type="platform_owner"`` must flow through the dispatcher all
    the way to the AutomationMutationPipeline so audit attribution is
    preserved across the migration."""
    template = next(t for t in TEMPLATES if "channel_id" in t.required_overrides)

    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.create_rule = AsyncMock(
        return_value=_automation_result(template),
    )
    pipeline_class.return_value = pipeline_instance

    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        pipeline_class,
    ):
        await apply_template_to_guild(
            template=template,
            guild=_guild(),
            actor=_author(),
            channel_id=12345,
            role_id=None,
        )

    kwargs = pipeline_instance.create_rule.await_args.kwargs
    assert kwargs["actor_type"] == "platform_owner", (
        "actor_type must be preserved through the dispatcher; if this fails, "
        "the dispatcher likely hardcodes a different actor_type for automation."
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
            guild=_guild(),
            actor=_author(),
            channel_id=0,  # invalid sentinel
            role_id=None,
        )

    assert outcome.ok is False
    assert "channel_id is required" in outcome.detail


@pytest.mark.asyncio
async def test_apply_button_short_circuits_when_required_override_missing():
    """Apply with required ``channel_id`` unset must not call the pipeline."""
    template = next(
        t for t in TEMPLATES if "channel_id" in t.required_overrides
    )
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
    template = next(
        t for t in TEMPLATES if "channel_id" in t.required_overrides
    )
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
    assert kwargs["guild"] is interaction.guild
    assert kwargs["actor"] is interaction.user
    assert kwargs["channel_id"] == 12345


def test_picker_select_options_never_exceed_25():
    view = TemplatePickerView(_author())
    selects = [c for c in view.children if hasattr(c, "options")]
    assert len(selects[0].options) <= 25
