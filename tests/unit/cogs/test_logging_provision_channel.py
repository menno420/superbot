"""Unit tests for the S7c logging create-channel flow.

Covers:

- :func:`build_preview_embed` calls
  :meth:`ResourceProvisioningPipeline.preview` and renders the
  result (allowed → green; blocked → orange + warnings field).
- :class:`LogChannelProvisionView` shape (Confirm + Cancel,
  invoker-locked).  Confirm button is disabled when the preview
  is not allowed.
- Confirm callback calls
  :meth:`ResourceProvisioningPipeline.provision(confirmed=True)`
  with the correct request shape (mode="create").
- Provisioning failure surfaces as an ephemeral error embed.
- Cancel produces an ephemeral cancellation embed and stops the view.
- DM invocation rejected.

The pipeline's auto-bind via :class:`BindingMutationPipeline` is
internal to ``ResourceProvisioningPipeline.provision`` (step 8) and
is exercised by the existing pipeline tests; here we verify the UI
calls the right pipeline method with the right args.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.logging.provision_view import (
    LogChannelProvisionView,
    _commit_provision,
    build_preview_embed,
)


def _author(id_: int = 1) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = id_
    return member


def _interaction(*, author: MagicMock, guild: object) -> MagicMock:
    interaction = MagicMock()
    interaction.user = author
    interaction.guild = guild
    interaction.response.send_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# build_preview_embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_allowed_returns_green_embed_and_allowed_true():
    guild = MagicMock(spec=discord.Guild)
    guild.id = 7

    fake_preview = MagicMock()
    fake_preview.allowed = True
    fake_preview.action = "create_new"
    fake_preview.target_name = "bot-mod-log"
    fake_preview.warnings = ()

    fake_pipeline = MagicMock()
    fake_pipeline.preview = AsyncMock(return_value=fake_preview)

    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        return_value=fake_pipeline,
    ):
        embed, allowed = await build_preview_embed(guild, "mod")
    assert allowed is True
    assert embed.color == discord.Color.green()
    fake_pipeline.preview.assert_awaited_once()
    field_names = [f.name for f in embed.fields]
    assert "Action" in field_names
    assert "Target name" in field_names
    assert "Allowed" in field_names
    # No "Warnings" field when warnings is empty.
    assert "Warnings" not in field_names


@pytest.mark.asyncio
async def test_preview_blocked_shows_warnings_and_orange_color():
    guild = MagicMock(spec=discord.Guild)
    guild.id = 7

    fake_preview = MagicMock()
    fake_preview.allowed = False
    fake_preview.action = "blocked"
    fake_preview.target_name = ""
    fake_preview.warnings = (
        "missing manage_channels permission",
        "slot already bound",
    )

    fake_pipeline = MagicMock()
    fake_pipeline.preview = AsyncMock(return_value=fake_preview)

    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        return_value=fake_pipeline,
    ):
        embed, allowed = await build_preview_embed(guild, "cleanup")
    assert allowed is False
    assert embed.color == discord.Color.orange()
    warnings_field = next(f for f in embed.fields if f.name == "Warnings")
    assert "manage_channels permission" in warnings_field.value
    assert "slot already bound" in warnings_field.value


@pytest.mark.asyncio
async def test_preview_invalid_kind_raises():
    guild = MagicMock(spec=discord.Guild)
    with pytest.raises(ValueError):
        await build_preview_embed(guild, "garbage")


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_view_has_confirm_and_cancel_button():
    view = LogChannelProvisionView(_author(), "mod", confirm_enabled=True)
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    labels = [b.label or "" for b in buttons]
    assert any("Confirm" in lbl for lbl in labels)
    assert any("Cancel" in lbl for lbl in labels)


def test_view_confirm_button_disabled_when_not_allowed():
    view = LogChannelProvisionView(_author(), "cleanup", confirm_enabled=False)
    confirm = next(
        b
        for b in view.children
        if isinstance(b, discord.ui.Button) and "Confirm" in (b.label or "")
    )
    assert confirm.disabled is True


def test_view_kind_unknown_raises():
    with pytest.raises(ValueError):
        LogChannelProvisionView(_author(), "garbage", confirm_enabled=True)


@pytest.mark.asyncio
async def test_view_invoker_check_rejects_other_user():
    view = LogChannelProvisionView(_author(id_=42), "mod", confirm_enabled=True)
    interaction = MagicMock()
    interaction.user.id = 99
    interaction.response.send_message = AsyncMock()
    result = await view.interaction_check(interaction)
    assert result is False


# ---------------------------------------------------------------------------
# Confirm callback — routes through ResourceProvisioningPipeline.provision
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_commit_provision_calls_pipeline_with_confirmed_true_for_mod():
    actor = _author()
    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    interaction = _interaction(author=actor, guild=guild)

    fake_result = MagicMock()
    fake_result.resource_id = 500
    fake_result.outcome = "created"
    fake_result.binding_written = True
    fake_result.audit_id = 1
    fake_pipeline = MagicMock()
    fake_pipeline.provision = AsyncMock(return_value=fake_result)

    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        return_value=fake_pipeline,
    ):
        await _commit_provision(interaction, kind="mod")

    fake_pipeline.provision.assert_awaited_once()
    args = fake_pipeline.provision.await_args
    # Pipeline.provision(guild, request, actor, confirmed=True)
    assert args.args[0] is guild
    assert args.args[1].subsystem == "logging"
    assert args.args[1].binding_name == "mod_channel"
    assert args.args[1].mode == "create"
    assert args.args[2] is actor
    assert args.kwargs.get("confirmed") is True


@pytest.mark.asyncio
async def test_commit_provision_routes_cleanup_to_cleanup_channel():
    actor = _author()
    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    interaction = _interaction(author=actor, guild=guild)

    fake_result = MagicMock()
    fake_result.resource_id = 600
    fake_result.outcome = "created"
    fake_result.binding_written = True
    fake_result.audit_id = 2
    fake_pipeline = MagicMock()
    fake_pipeline.provision = AsyncMock(return_value=fake_result)

    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        return_value=fake_pipeline,
    ):
        await _commit_provision(interaction, kind="cleanup")

    assert fake_pipeline.provision.await_args.args[1].binding_name == "cleanup_channel"


@pytest.mark.asyncio
async def test_commit_provision_rejects_dm_invocation():
    interaction = _interaction(author=_author(), guild=None)

    await _commit_provision(interaction, kind="mod")

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "guild context" in msg


@pytest.mark.asyncio
async def test_commit_provision_surfaces_pipeline_error_ephemerally():
    from services.resource_provisioning import ResourceProvisioningError

    actor = _author()
    guild = MagicMock(spec=discord.Guild)
    guild.id = 7
    interaction = _interaction(author=actor, guild=guild)

    fake_pipeline = MagicMock()
    fake_pipeline.provision = AsyncMock(
        side_effect=ResourceProvisioningError("missing manage_channels"),
    )

    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        return_value=fake_pipeline,
    ):
        await _commit_provision(interaction, kind="mod")

    interaction.response.send_message.assert_awaited_once()
    sent = interaction.response.send_message.await_args
    assert sent.kwargs.get("ephemeral") is True
    msg = sent.args[0]
    assert "ResourceProvisioningError" in msg
    assert "manage_channels" in msg


# ---------------------------------------------------------------------------
# Cancel callback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_button_sends_cancellation_and_stops_view():
    view = LogChannelProvisionView(_author(), "mod", confirm_enabled=True)
    cancel = next(
        b
        for b in view.children
        if isinstance(b, discord.ui.Button) and "Cancel" in (b.label or "")
    )
    interaction = MagicMock()
    interaction.user = view._author
    interaction.response.send_message = AsyncMock()

    await cancel.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    sent = interaction.response.send_message.await_args
    assert sent.kwargs.get("ephemeral") is True
    embed = sent.kwargs.get("embed")
    assert embed is not None
    assert "Cancel" in (embed.title or "")
    assert view.is_finished()
