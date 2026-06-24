"""Tests for the ticket config panel — the no-typing setup UI.

Pins: role + channel pickers are native dropdowns (no free text); Enable writes
through the audited ``ticket_mutation.update_config`` and refuses without a staff
role; Auto-create delegates to ``ticket_mutation.create_log_channel`` and adopts
the returned channel (or surfaces failure); Post panel requires tickets enabled;
``open_ticket_config_panel`` seeds the view from current config.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.tickets import TicketConfigPanelView
from views.tickets import config_panel as cp


def _interaction(guild_id: int = 1):
    i = MagicMock()
    i.user = SimpleNamespace(id=99)
    i.guild = SimpleNamespace(id=guild_id, get_channel=lambda _id: None)
    i.response = MagicMock()
    i.response.send_message = AsyncMock()
    i.response.edit_message = AsyncMock()
    i.followup = MagicMock()
    i.followup.send = AsyncMock()
    return i


def _button(view: TicketConfigPanelView, label_sub: str) -> discord.ui.Button:
    return next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and label_sub in (c.label or "")
    )


def test_embed_names_tickets_and_flags_required_role():
    embed = cp.build_ticket_config_embed()
    blob = ((embed.title or "") + (embed.description or "")).lower()
    assert "ticket" in blob
    field = next(f for f in embed.fields if f.name in ("Selected", "Current"))
    assert "required" in field.value.lower()


def test_panel_uses_native_dropdowns_not_free_text():
    view = TicketConfigPanelView(SimpleNamespace(id=99))
    type_names = {type(c).__name__ for c in view.children}
    assert any("RoleSelect" in t for t in type_names)
    assert any("ChannelSelect" in t for t in type_names)


@pytest.mark.asyncio
async def test_enable_refuses_without_staff_role():
    view = TicketConfigPanelView(SimpleNamespace(id=99))
    i = _interaction()
    with patch.object(
        cp.ticket_mutation, "update_config", new_callable=AsyncMock
    ) as up:
        await _button(view, "Enable").callback(i)
    up.assert_not_awaited()
    i.response.send_message.assert_awaited_once()
    assert "staff role" in i.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_enable_writes_through_audited_update_config():
    view = TicketConfigPanelView(
        SimpleNamespace(id=99), staff_role_id=555, log_channel_id=777
    )
    i = _interaction()
    with patch.object(
        cp.ticket_mutation, "update_config", new_callable=AsyncMock
    ) as up:
        await _button(view, "Enable").callback(i)
    up.assert_awaited_once()
    assert up.await_args.kwargs["enabled"] is True
    assert up.await_args.kwargs["staff_role_id"] == 555
    assert up.await_args.kwargs["log_channel_id"] == 777
    assert up.await_args.args == (1, 99)
    i.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_autocreate_log_delegates_and_adopts_channel():
    view = TicketConfigPanelView(SimpleNamespace(id=99), staff_role_id=555)
    i = _interaction()
    result = cp.ticket_mutation.TicketChannelResult(
        True, "made it", channel_id=4242
    )
    with patch.object(
        cp.ticket_mutation,
        "create_log_channel",
        new_callable=AsyncMock,
        return_value=result,
    ) as cr:
        await _button(view, "Auto-create").callback(i)
    cr.assert_awaited_once()
    assert cr.await_args.kwargs["staff_role_id"] == 555
    assert view.log_channel_id == 4242
    i.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_autocreate_log_surfaces_failure_without_adopting():
    view = TicketConfigPanelView(SimpleNamespace(id=99))
    i = _interaction()
    result = cp.ticket_mutation.TicketChannelResult(False, "need Manage Channels")
    with patch.object(
        cp.ticket_mutation,
        "create_log_channel",
        new_callable=AsyncMock,
        return_value=result,
    ):
        await _button(view, "Auto-create").callback(i)
    i.response.send_message.assert_awaited_once()
    assert "manage channels" in i.response.send_message.await_args.args[0].lower()
    assert view.log_channel_id is None


@pytest.mark.asyncio
async def test_post_panel_requires_enabled():
    view = TicketConfigPanelView(SimpleNamespace(id=99))  # enabled defaults False
    i = _interaction()
    await _button(view, "Post").callback(i)
    i.response.send_message.assert_awaited_once()
    assert "enable" in i.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_open_ticket_config_panel_seeds_from_config():
    cfg = SimpleNamespace(
        enabled=True, staff_role_id=9, log_channel_id=5, max_open_per_user=4
    )
    guild = SimpleNamespace(
        id=1,
        get_channel=lambda _id: None,
        get_role=lambda _id: SimpleNamespace(mention="@Staff"),
    )
    with patch.object(
        cp.ticket_service, "get_config", new_callable=AsyncMock, return_value=cfg
    ):
        embed, view = await cp.open_ticket_config_panel(
            SimpleNamespace(id=99), guild=guild
        )
    assert isinstance(view, TicketConfigPanelView)
    assert view.staff_role_id == 9
    assert view.log_channel_id == 5
    assert "🎫" in (embed.title or "")
