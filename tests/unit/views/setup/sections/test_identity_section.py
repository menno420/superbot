"""Behavior tests for the Identity & defaults setup section.

Pins:

* The section is registered and reachable via the registry.
* ``run()`` renders the identity snapshot ephemerally, instantiates
  ``IdentitySectionView``, and marks the session step.
* The warn-threshold modal validates input and rejects non-positive
  integers without staging a SetupOperation.
* On valid input, the modal appends exactly one
  ``SetupOperation(kind="set_setting", subsystem="moderation",
  setting_name="warn_threshold", value=<int>)`` to the per-guild
  draft via :mod:`services.setup_draft`, with canonical metadata
  (source=manual, confidence=high, risk=low).
* The modal **does not** call :func:`services.setup_operations.apply_operations`
  directly — Final Review owns the apply path.
* On draft-append failure, the operator sees an error and the
  session is NOT marked progressed.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.setup_sections import REGISTRY
from views.setup.sections import identity as identity_section


def _owner(guild_owner_id: int = 99):
    member = MagicMock(spec=discord.Member)
    member.id = guild_owner_id
    member.guild = SimpleNamespace(owner_id=guild_owner_id)
    member.guild_permissions = SimpleNamespace(administrator=False)
    return member


def _guild():
    guild = MagicMock()
    guild.id = 1
    guild.name = "Test Server"
    guild.owner = SimpleNamespace(display_name="Alice", name="alice")
    guild.member_count = 42
    return guild


def _interaction(guild=None):
    interaction = MagicMock()
    interaction.user = _owner()
    interaction.guild_id = 1
    interaction.guild = guild if guild is not None else _guild()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    return interaction


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_identity_section_registered_with_expected_slug():
    section = REGISTRY.get(identity_section.SLUG)
    assert section is not None
    assert section.slug == "identity"


def test_identity_section_uses_writable_moderation_setting():
    assert identity_section.SETTING_SUBSYSTEM == "moderation"
    assert identity_section.SETTING_NAME == "warn_threshold"


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_rejects_dm_context():
    interaction = _interaction(guild=None)
    interaction.guild = None
    await identity_section.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "guild" in msg


@pytest.mark.asyncio
async def test_run_renders_identity_panel_and_marks_progress():
    interaction = _interaction()
    with (
        patch.object(
            identity_section,
            "_read_current_warn_threshold",
            new_callable=AsyncMock,
            return_value=3,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await identity_section.run(interaction, MagicMock())

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs["view"], identity_section.IdentitySectionView)
    embed = kwargs["embed"]
    rendered = "\n".join(f.value or "" for f in embed.fields)
    assert "Test Server" in rendered
    assert "3" in rendered  # current warn threshold value
    mark_mock.assert_awaited_once_with(1, step="identity")


# ---------------------------------------------------------------------------
# Modal validation
# ---------------------------------------------------------------------------


def _modal_with_value(text: str) -> identity_section._WarnThresholdModal:
    modal = identity_section._WarnThresholdModal(MagicMock())
    modal.threshold = SimpleNamespace(value=text)  # type: ignore[assignment]
    return modal


@pytest.mark.asyncio
async def test_modal_rejects_non_integer():
    modal = _modal_with_value("not-a-number")
    interaction = _interaction()
    with patch(
        "services.setup_draft.append",
        new_callable=AsyncMock,
    ) as append_mock:
        await modal.on_submit(interaction)
    interaction.response.send_message.assert_awaited_once()
    assert "valid integer" in interaction.response.send_message.await_args.args[0]
    append_mock.assert_not_called()


@pytest.mark.asyncio
async def test_modal_rejects_non_positive_integer():
    modal = _modal_with_value("0")
    interaction = _interaction()
    with patch(
        "services.setup_draft.append",
        new_callable=AsyncMock,
    ) as append_mock:
        await modal.on_submit(interaction)
    interaction.response.send_message.assert_awaited_once()
    assert "positive" in interaction.response.send_message.await_args.args[0].lower()
    append_mock.assert_not_called()


@pytest.mark.asyncio
async def test_modal_rejects_dm_context():
    modal = _modal_with_value("5")
    interaction = _interaction(guild=None)
    interaction.guild = None
    with patch(
        "services.setup_draft.append",
        new_callable=AsyncMock,
    ) as append_mock:
        await modal.on_submit(interaction)
    interaction.response.send_message.assert_awaited_once()
    append_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Modal draft-append path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_modal_appends_set_setting_to_draft_store():
    modal = _modal_with_value("5")
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await modal.on_submit(interaction)

    append_mock.assert_awaited_once()
    op = append_mock.await_args.args[0]
    assert op.kind == "set_setting"
    assert op.subsystem == "moderation"
    assert op.setting_name == "warn_threshold"
    assert op.value == 5
    kwargs = append_mock.await_args.kwargs
    assert kwargs["guild_id"] == 1
    assert kwargs["actor_id"] == 99
    assert "warn_threshold = 5" in kwargs["label"]
    md = kwargs["metadata"]
    assert md["source"] == "manual"
    assert md["confidence"] == "high"
    assert md["risk"] == "low"
    assert "Operator entered" in md["reason"]


@pytest.mark.asyncio
async def test_modal_confirmation_includes_pending_count():
    modal = _modal_with_value("5")
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=3,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await modal.on_submit(interaction)
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "Staged for Final review" in msg
    assert "warn threshold = 5" in msg
    assert "3" in msg  # pending count


@pytest.mark.asyncio
async def test_modal_does_not_call_apply_operations_or_settings_pipeline():
    """After the draft-first migration, the modal must not apply
    anything directly.  Both ``apply_operations`` and the
    ``SettingsMutationPipeline`` constructor stay untouched.
    """
    modal = _modal_with_value("7")
    interaction = _interaction()
    pipeline_ctor = MagicMock()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_operations.apply_operations",
            new_callable=AsyncMock,
        ) as apply_mock,
        patch(
            "services.settings_mutation.SettingsMutationPipeline",
            pipeline_ctor,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await modal.on_submit(interaction)
    apply_mock.assert_not_called()
    pipeline_ctor.assert_not_called()


@pytest.mark.asyncio
async def test_modal_surfaces_append_failure_and_does_not_mark_progress():
    modal = _modal_with_value("5")
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB explosion"),
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await modal.on_submit(interaction)
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "stage" in msg.lower()
    mark_mock.assert_not_called()


@pytest.mark.asyncio
async def test_modal_tolerates_count_failure_in_confirmation():
    """A failure in setup_draft.count is logged but doesn't propagate;
    the operator still gets a "Staged" message with pending=0.
    """
    modal = _modal_with_value("5")
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            side_effect=RuntimeError("count failed"),
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await modal.on_submit(interaction)
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "Staged for Final review" in msg
