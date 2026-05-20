"""Unit tests for the S7 binding-edit widget.

Covers :class:`views.settings.edit_binding.BindingEditView` and its
write paths, independent of ``SubsystemSettingsView`` dispatch (the
dispatch is exercised by ``test_settings_cog_edit_routes.py``).

Pins:

* The view rejects unsupported binding kinds at construction so the
  caller can fall back to a "not yet editable" message rather than
  silently rendering an empty view.
* ``_commit_binding`` routes through
  :class:`BindingMutationPipeline.set_binding`, never touching
  ``utils.db`` directly.
* ``BindingMutationError`` and arbitrary exceptions surface as
  ephemeral errors, NOT crashes that would leave the operator with
  an unresponsive panel.
* ``_commit_clear`` routes through
  :class:`BindingMutationPipeline.clear_binding`.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.settings.edit_binding import (
    BindingEditView,
    _commit_binding,
    _commit_clear,
)


def _interaction(*, guild_id: int = 1):
    interaction = MagicMock()
    interaction.guild = MagicMock(id=guild_id)
    interaction.guild.id = guild_id
    interaction.user = MagicMock(id=7)
    interaction.message = MagicMock(id=100)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _mutation_result(*, old: int | None = 50, new: int | None = 100):
    result = MagicMock()
    result.old_target_id = old
    result.new_target_id = new
    return result


def test_view_rejects_unsupported_kind():
    with pytest.raises(ValueError, match="member"):
        BindingEditView("logging", "mod_member", "member")


def test_view_with_channel_kind_hosts_channel_select_and_clear():
    view = BindingEditView("logging", "mod_channel", "channel")
    selects = [c for c in view.children if isinstance(c, discord.ui.ChannelSelect)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1
    assert len(buttons) == 1
    assert buttons[0].label == "Clear"


def test_view_with_role_kind_hosts_role_select_and_clear():
    view = BindingEditView("moderation", "trusted_role", "role")
    selects = [c for c in view.children if isinstance(c, discord.ui.RoleSelect)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1
    assert len(buttons) == 1
    assert buttons[0].label == "Clear"


def test_view_with_category_kind_narrows_channel_types_to_category():
    view = BindingEditView("admin", "ops_category", "category")
    select = next(c for c in view.children if isinstance(c, discord.ui.ChannelSelect))
    assert discord.ChannelType.category in select.channel_types


@pytest.mark.asyncio
async def test_commit_binding_routes_through_set_binding():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.set_binding = AsyncMock(return_value=_mutation_result())
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        pipeline_class,
    ):
        await _commit_binding(
            interaction,
            "logging",
            "mod_channel",
            "channel",
            12345,
            None,
        )

    pipeline_instance.set_binding.assert_awaited_once()
    args, kwargs = pipeline_instance.set_binding.call_args
    # set_binding(guild, subsystem, binding_name, kind, target_id, actor)
    assert args[1] == "logging"
    assert args[2] == "mod_channel"
    assert args[4] == 12345
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "Bound `logging.mod_channel`" in msg
    assert "<#12345>" in msg


@pytest.mark.asyncio
async def test_commit_binding_rejects_dm_context():
    interaction = _interaction()
    interaction.guild = None
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.set_binding = AsyncMock()
    pipeline_class.return_value = pipeline_instance

    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        pipeline_class,
    ):
        await _commit_binding(
            interaction,
            "logging",
            "mod_channel",
            "channel",
            12345,
            None,
        )

    pipeline_instance.set_binding.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    assert "guild" in interaction.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_commit_binding_surfaces_pipeline_error_ephemerally():
    from services.binding_mutation import UndeclaredBindingError

    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.set_binding = AsyncMock(
        side_effect=UndeclaredBindingError("no such binding"),
    )
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        pipeline_class,
    ):
        await _commit_binding(
            interaction,
            "logging",
            "mod_channel",
            "channel",
            12345,
            None,
        )

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "UndeclaredBindingError" in msg
    assert "no such binding" in msg


@pytest.mark.asyncio
async def test_commit_binding_surfaces_unexpected_error_ephemerally():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.set_binding = AsyncMock(side_effect=RuntimeError("kaboom"))
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        pipeline_class,
    ):
        await _commit_binding(
            interaction,
            "logging",
            "mod_channel",
            "channel",
            12345,
            None,
        )

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "Unexpected error" in msg
    assert "RuntimeError" in msg


@pytest.mark.asyncio
async def test_commit_clear_routes_through_clear_binding():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.clear_binding = AsyncMock(
        return_value=_mutation_result(old=999, new=None),
    )
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        pipeline_class,
    ):
        await _commit_clear(
            interaction,
            "logging",
            "mod_channel",
            "channel",
            None,
        )

    pipeline_instance.clear_binding.assert_awaited_once()
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "Cleared `logging.mod_channel`" in msg
    assert "999" in msg


@pytest.mark.asyncio
async def test_commit_clear_rejects_unknown_kind():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.clear_binding = AsyncMock()
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        pipeline_class,
    ):
        await _commit_clear(
            interaction,
            "logging",
            "mod_channel",
            "not_a_real_kind",
            None,
        )

    pipeline_instance.clear_binding.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    assert "Unknown" in interaction.response.send_message.await_args.args[0]
