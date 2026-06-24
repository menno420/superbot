"""Tests for Essential Setup — the plain-language, direct-apply setup spine.

Pins:
* Flow navigation: advance / back / current_view / step counter / summary.
* Each step applies its config IMMEDIATELY through the audited
  ``SettingsMutationPipeline`` (direct lane) — and refuses (no write) until the
  required pick is made.
* The entry point is admin-gated and server-only.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.runtime.subsystem_schema import BindingKind
from views.setup import essential_setup as es


def _member(admin: bool = True):
    return SimpleNamespace(
        id=99,
        guild_permissions=SimpleNamespace(administrator=admin),
    )


def _guild(gid: int = 1):
    return SimpleNamespace(id=gid, name="Test")


def _interaction():
    interaction = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


@pytest.fixture
def pipeline():
    # The pipeline is imported lazily inside the step (setup views must not
    # import mutation pipelines at top level), so patch it at its source.
    with patch("services.settings_mutation.SettingsMutationPipeline") as cls:
        cls.return_value.set_value = AsyncMock()
        yield cls.return_value


@pytest.fixture
def binding_pipeline():
    # BindingMutationPipeline is also lazy-imported inside the log-channel step
    # (no-top-level-pipeline-import invariant) — patch at its source.
    with patch("services.binding_mutation.BindingMutationPipeline") as cls:
        cls.return_value.set_binding = AsyncMock()
        yield cls.return_value


@pytest.fixture
def channel_service():
    # ChannelLifecycleService (auto-create) is lazy-imported inside the step.
    with patch(
        "services.channel_lifecycle_service.ChannelLifecycleService",
    ) as cls:
        cls.return_value.create_channels = AsyncMock()
        yield cls.return_value


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


def test_flow_counter_and_navigation():
    flow = es.EssentialFlow(_member(), _guild())
    assert flow.total == 5
    assert flow.step_counter() == "Step 1 of 5"
    expected = [
        es.GreetMembersStep,
        es.ModeratorsStep,
        es.BlockSpamStep,
        es.LogChannelStep,
        es.HelpDeskStep,
    ]
    for i, cls in enumerate(expected):
        assert flow.step_counter() == f"Step {i + 1} of 5"
        assert isinstance(flow.current_view(), cls)
        flow.advance()

    assert flow.done
    assert isinstance(flow.current_view(), es.EssentialSummaryView)

    flow.back()
    assert isinstance(flow.current_view(), es.HelpDeskStep)


def test_first_step_has_no_back_button():
    flow = es.EssentialFlow(_member(), _guild())
    step = es.GreetMembersStep(flow)
    assert not any(isinstance(c, es._BackButton) for c in step.children)
    # the second step does get a Back button
    flow.advance()
    step2 = es.ModeratorsStep(flow)
    assert any(isinstance(c, es._BackButton) for c in step2.children)


# ---------------------------------------------------------------------------
# Greet members
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_greet_requires_channel_before_applying(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    step = es.GreetMembersStep(flow)
    interaction = _interaction()

    await step.apply(interaction)

    pipeline.set_value.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    assert "channel" in interaction.response.send_message.await_args.args[0].lower()
    assert flow.index == 0  # did not advance


@pytest.mark.asyncio
async def test_greet_applies_welcome_settings_and_advances(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    step = es.GreetMembersStep(flow)
    step.channel_id = 555
    step.entry_role_id = 777
    interaction = _interaction()

    await step.apply(interaction)

    # enabled + join_enabled + channel + entry_role = 4 immediate writes
    assert pipeline.set_value.await_count == 4
    subsystems = {c.args[1] for c in pipeline.set_value.await_args_list}
    names = {c.args[2] for c in pipeline.set_value.await_args_list}
    assert subsystems == {"welcome"}
    assert {"enabled", "join_enabled", "channel", "entry_role"} == names
    assert flow.index == 1  # advanced
    assert flow.applied and "555" in flow.applied[0]


@pytest.mark.asyncio
async def test_greet_without_role_writes_three_settings(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    step = es.GreetMembersStep(flow)
    step.channel_id = 555
    await step.apply(_interaction())
    assert pipeline.set_value.await_count == 3


# ---------------------------------------------------------------------------
# Moderators
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moderators_requires_role(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    step = es.ModeratorsStep(flow)
    interaction = _interaction()
    await step.apply(interaction)
    pipeline.set_value.assert_not_awaited()
    assert flow.index == 0


@pytest.mark.asyncio
async def test_moderators_applies_role_and_dm(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    step = es.ModeratorsStep(flow)
    step.mod_role_id = 4242
    await step.apply(_interaction())
    assert pipeline.set_value.await_count == 2
    calls = {(c.args[1], c.args[2]) for c in pipeline.set_value.await_args_list}
    assert ("moderation", "moderator_role") in calls
    assert ("moderation", "dm_on_action") in calls
    assert flow.index == 1


# ---------------------------------------------------------------------------
# Block spam
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_block_spam_applies_automod_with_all_filters(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 2
    step = es.BlockSpamStep(flow)
    await step.apply(_interaction())
    # enabled + 4 filters = 5 immediate writes, all to automod
    assert pipeline.set_value.await_count == 5
    subsystems = {c.args[1] for c in pipeline.set_value.await_args_list}
    assert subsystems == {"automod"}
    names = {c.args[2] for c in pipeline.set_value.await_args_list}
    assert names == {
        "enabled",
        "spam_enabled",
        "invites_enabled",
        "caps_enabled",
        "mentions_enabled",
    }
    assert flow.index == 3


@pytest.mark.asyncio
async def test_block_spam_respects_toggled_off_filter(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 2
    step = es.BlockSpamStep(flow)
    step.filters["caps_enabled"] = False
    await step.apply(_interaction())
    by_name = {c.args[2]: c.args[3] for c in pipeline.set_value.await_args_list}
    assert by_name["caps_enabled"] is False
    assert by_name["spam_enabled"] is True


# ---------------------------------------------------------------------------
# Choose a log channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_log_channel_requires_a_pick_or_create(
    pipeline,
    binding_pipeline,
    channel_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 3
    step = es.LogChannelStep(flow)
    interaction = _interaction()

    await step.apply(interaction)

    # Nothing picked and auto-create off → no writes, no advance.
    pipeline.set_value.assert_not_awaited()
    binding_pipeline.set_binding.assert_not_awaited()
    channel_service.create_channels.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    assert "channel" in interaction.response.send_message.await_args.args[0].lower()
    assert flow.index == 3


@pytest.mark.asyncio
async def test_log_channel_binds_picked_channel_and_advances(pipeline, binding_pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 3
    step = es.LogChannelStep(flow)
    step.channel_id = 8800

    await step.apply(_interaction())

    # logging.enabled flipped on through the settings pipeline …
    assert ("logging", "enabled") in {
        (c.args[1], c.args[2]) for c in pipeline.set_value.await_args_list
    }
    # … and mod_channel bound to the picked channel through the binding pipeline.
    binding_pipeline.set_binding.assert_awaited_once()
    args = binding_pipeline.set_binding.await_args.args
    assert args[1] == "logging"
    assert args[2] == "mod_channel"
    assert args[3] == BindingKind.CHANNEL
    assert args[4] == 8800
    assert flow.index == 4
    assert flow.applied and "8800" in flow.applied[0]


@pytest.mark.asyncio
async def test_log_channel_auto_creates_then_binds(
    pipeline,
    binding_pipeline,
    channel_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 3
    step = es.LogChannelStep(flow)
    step.auto_create = True
    channel_service.create_channels.return_value = SimpleNamespace(
        applied=(SimpleNamespace(target_id=4321),),
        first_error="",
    )

    await step.apply(_interaction())

    channel_service.create_channels.assert_awaited_once()
    # the created channel id is bound, and the summary notes it was created.
    binding_pipeline.set_binding.assert_awaited_once()
    assert binding_pipeline.set_binding.await_args.args[4] == 4321
    assert flow.index == 4
    assert flow.applied and "created" in flow.applied[0].lower()


@pytest.mark.asyncio
async def test_log_channel_create_failure_blocks(
    pipeline,
    binding_pipeline,
    channel_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 3
    step = es.LogChannelStep(flow)
    step.auto_create = True
    channel_service.create_channels.return_value = SimpleNamespace(
        applied=(),
        first_error="missing permission",
    )
    interaction = _interaction()

    await step.apply(interaction)

    # Creation failed → surfaced an error, wrote nothing, did not advance.
    channel_service.create_channels.assert_awaited_once()
    binding_pipeline.set_binding.assert_not_awaited()
    pipeline.set_value.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    assert flow.index == 3


# ---------------------------------------------------------------------------
# Help desk
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_desk_requires_staff_role():
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 4
    step = es.HelpDeskStep(flow)
    interaction = _interaction()
    with patch("services.ticket_mutation.update_config", new=AsyncMock()) as upd:
        await step.apply(interaction)
    upd.assert_not_awaited()
    assert flow.index == 4
    assert "staff" in interaction.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_help_desk_enables_tickets_and_advances():
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 4
    step = es.HelpDeskStep(flow)
    step.staff_role_id = 321
    step.log_channel_id = 654
    with patch("services.ticket_mutation.update_config", new=AsyncMock()) as upd:
        await step.apply(_interaction())
    upd.assert_awaited_once()
    kwargs = upd.await_args.kwargs
    assert kwargs["enabled"] is True
    assert kwargs["staff_role_id"] == 321
    assert kwargs["log_channel_id"] == 654
    assert flow.index == 5


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def test_summary_lists_applied_changes():
    flow = es.EssentialFlow(_member(), _guild())
    flow.record_applied("Greetings on")
    flow.record_applied("Moderator role set")
    embed = es.EssentialSummaryView(flow).render()
    blob = (embed.description or "") + " ".join(f.value for f in embed.fields)
    assert "Greetings on" in blob
    assert "Moderator role set" in blob


# ---------------------------------------------------------------------------
# Entry gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_entry_rejects_dm():
    interaction = _interaction()
    interaction.guild = None
    interaction.user = _member()
    await es.open_essential_setup(interaction)
    interaction.response.send_message.assert_awaited_once()
    assert "server" in interaction.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_entry_rejects_non_admin():
    interaction = _interaction()
    interaction.guild = _guild()
    member = MagicMock()
    member.guild_permissions.administrator = False
    interaction.user = member
    # isinstance(member, discord.Member) must hold for the admin branch; patch it.
    with patch.object(es.discord, "Member", MagicMock):
        await es.open_essential_setup(interaction)
    interaction.response.send_message.assert_awaited_once()
    assert "admin" in interaction.response.send_message.await_args.args[0].lower()
