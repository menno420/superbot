"""PR-6 — Settings Manager: Command Access panel tests.

Pins:

* :func:`build_command_access_embed` renders the current policy
  via ``services.command_access_service.get_policy_snapshot`` and
  surfaces the recovery banner under ``disabled_except_bootstrap``.
* Mode-button callbacks route mutations through
  ``services.command_access_service.set_mode``; the channel select
  routes through ``replace_allowed_channels``.  Non-admin invokers
  are rejected with ephemeral feedback BEFORE the service is
  touched.
* Settings-hub button installation: the hub view exposes the new
  "Command access" button on the existing button row.

The service layer is patched per-test so the panel exercise stays
DB-free.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from utils.guild_config_accessors import CommandAccessPolicySnapshot
from views.settings.edit_command_access import (
    CommandAccessView,
    _apply_mode,
    _ChannelAllowlistSelect,
    build_command_access_embed,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _snapshot(
    mode: str | None,
    *channel_ids: int,
) -> CommandAccessPolicySnapshot:
    return CommandAccessPolicySnapshot(
        mode=mode,
        allowed_channels=frozenset(channel_ids),
    )


def _admin_user(user_id: int = 42) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        guild_permissions=SimpleNamespace(
            administrator=True,
            manage_guild=False,
        ),
    )


def _non_admin_user(user_id: int = 42) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        guild_permissions=SimpleNamespace(
            administrator=False,
            manage_guild=False,
        ),
    )


def _make_interaction(
    *,
    user=None,
    guild_id: int | None = 10,
):
    user = user or _admin_user()
    response = SimpleNamespace(
        send_message=AsyncMock(),
        defer=AsyncMock(),
        is_done=MagicMock(return_value=False),
    )
    followup = SimpleNamespace(send=AsyncMock())
    return SimpleNamespace(
        user=user,
        guild_id=guild_id,
        response=response,
        followup=followup,
        edit_original_response=AsyncMock(),
    )


# ---------------------------------------------------------------------------
# build_command_access_embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_for_unconfigured_guild_shows_default_label():
    """No DB policy row → embed labels the mode "All channels (default
    — no policy row)" so operators understand the implicit default
    rather than seeing a blank ``None``.
    """
    with patch(
        "services.command_access_service.get_policy_snapshot",
        new=AsyncMock(return_value=_snapshot(None)),
    ):
        embed = await build_command_access_embed(guild_id=10)
    text = " ".join(f.value for f in embed.fields)
    assert "All channels" in text
    assert "default" in text.lower()


@pytest.mark.asyncio
async def test_embed_for_selected_channels_lists_channel_mentions():
    with patch(
        "services.command_access_service.get_policy_snapshot",
        new=AsyncMock(return_value=_snapshot("selected_channels", 100, 200)),
    ):
        embed = await build_command_access_embed(guild_id=10)
    text = " ".join(f.value for f in embed.fields)
    assert "<#100>" in text
    assert "<#200>" in text


@pytest.mark.asyncio
async def test_embed_for_disabled_mode_includes_recovery_field():
    """Operators in ``disabled_except_bootstrap`` mode must see the
    explicit recovery path (mode button or ``!setup``) so the panel
    is self-rescuing.
    """
    with patch(
        "services.command_access_service.get_policy_snapshot",
        new=AsyncMock(return_value=_snapshot("disabled_except_bootstrap")),
    ):
        embed = await build_command_access_embed(guild_id=10)
    recovery_fields = [f for f in embed.fields if f.name == "Recovery"]
    assert len(recovery_fields) == 1
    assert "!setup" in recovery_fields[0].value


@pytest.mark.asyncio
async def test_embed_handles_missing_guild_context():
    """``guild_id=None`` (DM context) yields a placeholder embed
    rather than crashing the panel builder.
    """
    embed = await build_command_access_embed(guild_id=None)
    assert "Guild context" in " ".join(f.value for f in embed.fields)


# ---------------------------------------------------------------------------
# _apply_mode callback path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_mode_calls_service_for_admin():
    interaction = _make_interaction()
    view = CommandAccessView(interaction.user)

    with (
        patch(
            "services.command_access_service.set_mode",
            new=AsyncMock(),
        ) as mock_set_mode,
        patch(
            "services.command_access_service.get_policy_snapshot",
            new=AsyncMock(return_value=_snapshot("all_channels")),
        ),
    ):
        await _apply_mode(interaction, "all_channels", view)

    mock_set_mode.assert_awaited_once_with(
        guild_id=10,
        mode="all_channels",
        actor_id=42,
    )
    # Defers, refreshes the panel embed, sends ephemeral confirmation.
    interaction.response.defer.assert_awaited_once()
    interaction.edit_original_response.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_mode_rejects_non_admin_without_touching_service():
    interaction = _make_interaction(user=_non_admin_user())
    view = CommandAccessView(interaction.user)

    with patch(
        "services.command_access_service.set_mode",
        new=AsyncMock(),
    ) as mock_set_mode:
        await _apply_mode(interaction, "all_channels", view)

    mock_set_mode.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "permission" in msg.lower()


@pytest.mark.asyncio
async def test_apply_mode_rejects_dm_context():
    interaction = _make_interaction(guild_id=None)
    view = CommandAccessView(interaction.user)

    with patch(
        "services.command_access_service.set_mode",
        new=AsyncMock(),
    ) as mock_set_mode:
        await _apply_mode(interaction, "all_channels", view)

    mock_set_mode.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_mode_surfaces_service_errors_ephemerally():
    """A ``CommandAccessMutationError`` from the service must reach
    the operator as ephemeral feedback rather than propagating into
    the view dispatcher (where it would be a generic "interaction
    failed").
    """
    from services.command_access_service import InvalidCommandAccessModeError

    interaction = _make_interaction()
    view = CommandAccessView(interaction.user)

    with patch(
        "services.command_access_service.set_mode",
        new=AsyncMock(side_effect=InvalidCommandAccessModeError("bad")),
    ):
        await _apply_mode(interaction, "all_channels", view)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "InvalidCommandAccessModeError" in msg


# ---------------------------------------------------------------------------
# _ChannelAllowlistSelect callback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_channel_select_routes_to_replace_allowed_channels():
    interaction = _make_interaction()
    view = CommandAccessView(interaction.user)
    select = next(
        item for item in view.children if isinstance(item, _ChannelAllowlistSelect)
    )
    select._values = [SimpleNamespace(id=100), SimpleNamespace(id=200)]
    # Make ``self.values`` return the patched list — discord.py
    # builds it from the interaction payload at runtime.
    select.values  # touch property — defaults to empty before patch  # noqa: B018
    # discord.py select.values is a property reading from internal
    # state; override it on the instance for the test.
    type(select).values = property(lambda self: self._values)

    with (
        patch(
            "services.command_access_service.replace_allowed_channels",
            new=AsyncMock(),
        ) as mock_replace,
        patch(
            "services.command_access_service.get_policy_snapshot",
            new=AsyncMock(return_value=_snapshot("selected_channels", 100, 200)),
        ),
    ):
        await select.callback(interaction)

    mock_replace.assert_awaited_once_with(
        guild_id=10,
        channel_ids=[100, 200],
        actor_id=42,
    )
    interaction.response.defer.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_channel_select_rejects_non_admin():
    interaction = _make_interaction(user=_non_admin_user())
    view = CommandAccessView(interaction.user)
    select = next(
        item for item in view.children if isinstance(item, _ChannelAllowlistSelect)
    )
    type(select).values = property(lambda self: [SimpleNamespace(id=100)])

    with patch(
        "services.command_access_service.replace_allowed_channels",
        new=AsyncMock(),
    ) as mock_replace:
        await select.callback(interaction)

    mock_replace.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# CommandAccessView shape
# ---------------------------------------------------------------------------


def test_view_exposes_three_mode_buttons_and_channel_select_and_back():
    """The view must expose exactly the contract the embed promises:
    one button per access mode, a multi-channel select, and the
    "Back to Hub" navigation.
    """
    view = CommandAccessView(_admin_user())
    custom_ids = {
        getattr(c, "custom_id", None)
        for c in view.children
        if isinstance(c, discord.ui.Item)
    }
    assert "settings_command_access.mode.all_channels" in custom_ids
    assert "settings_command_access.mode.selected_channels" in custom_ids
    assert "settings_command_access.mode.disabled_except_bootstrap" in custom_ids
    assert "settings_command_access.channels" in custom_ids
    assert "settings_command_access.back" in custom_ids


# ---------------------------------------------------------------------------
# SettingsHubView wiring
# ---------------------------------------------------------------------------


def test_hub_view_exposes_command_access_button():
    """The settings hub picks up the new Command Access entry point."""
    from views.settings.hub import SettingsHubView

    hub = SettingsHubView(_admin_user())
    custom_ids = {
        getattr(c, "custom_id", None)
        for c in hub.children
        if isinstance(c, discord.ui.Item)
    }
    assert "settings_hub.command_access" in custom_ids


@pytest.mark.asyncio
async def test_hub_command_access_button_opens_command_access_view():
    """Clicking the Command Access button on the hub swaps the panel
    to the Command Access view + its embed.
    """
    from views.settings.hub import SettingsHubView, _OpenCommandAccess

    hub = SettingsHubView(_admin_user())
    button = next(item for item in hub.children if isinstance(item, _OpenCommandAccess))

    interaction = _make_interaction()
    interaction.response = SimpleNamespace(
        edit_message=AsyncMock(),
        send_message=AsyncMock(),
    )

    with patch(
        "services.command_access_service.get_policy_snapshot",
        new=AsyncMock(return_value=_snapshot(None)),
    ):
        await button.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    assert isinstance(kwargs["view"], CommandAccessView)
