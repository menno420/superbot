"""Tests for ``views.setup.depth_panel`` — wizard depth picker."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.setup_session import SetupSession
from views.setup.depth_panel import DepthPanelView, build_depth_embed


def _owner_member(user_id: int = 99):
    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=user_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _interaction(*, guild_id: int = 1):
    interaction = MagicMock()
    interaction.user = _owner_member()
    interaction.guild_id = guild_id
    interaction.guild = MagicMock(id=guild_id, name="Test", owner_id=99)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


def _session(*, depth: str | None = None) -> SetupSession:
    return SetupSession(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        setup_status="pending",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
        depth=depth,
    )


def test_depth_embed_lists_three_modes():
    embed = build_depth_embed()
    field_names = {(f.name or "").lower() for f in embed.fields}
    assert any("quick" in n for n in field_names)
    assert any("standard" in n for n in field_names)
    assert any("advanced" in n for n in field_names)


def test_depth_panel_has_three_buttons():
    view = DepthPanelView(_owner_member())
    custom_ids = {
        c.custom_id for c in view.children if isinstance(c, discord.ui.Button)
    }
    assert custom_ids == {
        "setup_depth:quick",
        "setup_depth:standard",
        "setup_depth:advanced",
    }


def test_depth_panel_highlights_current_choice():
    """When session.depth is set, the matching button is styled in
    success colour to surface the existing pick.
    """
    view = DepthPanelView(_owner_member(), session=_session(depth="standard"))
    by_id = {c.custom_id: c for c in view.children if isinstance(c, discord.ui.Button)}
    assert by_id["setup_depth:standard"].style is discord.ButtonStyle.success
    assert by_id["setup_depth:quick"].style is discord.ButtonStyle.secondary
    assert by_id["setup_depth:advanced"].style is discord.ButtonStyle.secondary


@pytest.mark.asyncio
async def test_depth_panel_select_persists_and_opens_hub():
    """Clicking a depth button persists it and edits the message to
    the hub view in place.
    """
    from views.setup.hub import SetupHubView

    view = DepthPanelView(_owner_member(), session=_session())
    interaction = _interaction()

    with (
        patch(
            "views.setup.depth_panel.setup_session.set_depth",
            new_callable=AsyncMock,
        ) as set_depth_mock,
        patch(
            "views.setup.depth_panel.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(depth="standard"),
        ),
        patch(
            "services.setup_draft.list_ops",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        await view._select(interaction, "standard")

    set_depth_mock.assert_awaited_once_with(1, "standard")
    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    assert isinstance(kwargs.get("view"), SetupHubView)


@pytest.mark.asyncio
async def test_depth_panel_select_after_wizard_transitions_to_wizard():
    """With after='wizard' (the first-run wizard entry), selecting a depth
    persists it and transitions the anchor into the linear wizard via
    render_wizard_step — not the hub.
    """
    view = DepthPanelView(_owner_member(), session=_session(), after="wizard")
    interaction = _interaction()

    with (
        patch(
            "views.setup.depth_panel.setup_session.set_depth",
            new_callable=AsyncMock,
        ) as set_depth_mock,
        patch(
            "views.setup.depth_panel.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(depth="quick"),
        ),
        patch(
            "views.setup.wizard_nav.render_wizard_step",
            new_callable=AsyncMock,
            return_value=True,
        ) as render_mock,
    ):
        await view._select(interaction, "quick")

    set_depth_mock.assert_awaited_once_with(1, "quick")
    render_mock.assert_awaited_once()
    assert render_mock.await_args.kwargs["step_index"] == 0


@pytest.mark.asyncio
async def test_depth_panel_select_handles_set_depth_failure():
    view = DepthPanelView(_owner_member(), session=_session())
    interaction = _interaction()

    with patch(
        "views.setup.depth_panel.setup_session.set_depth",
        new_callable=AsyncMock,
        side_effect=RuntimeError("db down"),
    ):
        await view._select(interaction, "quick")

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_depth_panel_select_requires_guild_context():
    view = DepthPanelView(_owner_member(), session=_session())
    interaction = _interaction()
    interaction.guild = None
    interaction.guild_id = None

    await view._select(interaction, "quick")

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "guild" in msg.lower()
