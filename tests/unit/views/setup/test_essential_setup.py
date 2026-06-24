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


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


def test_flow_counter_and_navigation():
    flow = es.EssentialFlow(_member(), _guild())
    assert flow.total == 2
    assert flow.step_counter() == "Step 1 of 2"
    assert isinstance(flow.current_view(), es.GreetMembersStep)

    flow.advance()
    assert flow.step_counter() == "Step 2 of 2"
    assert isinstance(flow.current_view(), es.ModeratorsStep)

    flow.advance()
    assert flow.done
    assert isinstance(flow.current_view(), es.EssentialSummaryView)

    flow.back()
    assert isinstance(flow.current_view(), es.ModeratorsStep)


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
