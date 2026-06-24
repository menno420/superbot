"""Tests for the support-tickets setup section.

Pins:

* Registration: slug, order, emoji, style, depth, and that ``customize``
  is wired so the guided-wizard Customize button is enabled.
* The embed names tickets and renders the staff role / log selection.
* ``_open_panel`` rejects DM context and opens the config panel in a guild.
* The Enable button writes through the audited ``ticket_mutation.update_config``
  (direct lane) with ``enabled=True`` + the selected role/log — and refuses
  (no write) until a staff role is chosen.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.setup_sections import REGISTRY
from views.setup.sections import ticket


def _interaction(guild_id: int = 1):
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild_id = guild_id
    interaction.guild = SimpleNamespace(
        id=guild_id, name="Test", get_channel=lambda _id: None
    )
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


def _enable_button(view: ticket.TicketSetupSectionView) -> discord.ui.Button:
    return next(c for c in view.children if isinstance(c, discord.ui.Button))


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_ticket_section_registered_with_expected_metadata():
    section = REGISTRY.get("ticket")
    assert section is not None
    assert section.slug == "ticket"
    assert section.order == 72
    assert section.emoji == "🎫"
    assert section.style == discord.ButtonStyle.secondary
    # Standard/advanced — not a "quick" essential.
    assert "quick" not in section.depths
    assert {"standard", "advanced"} <= section.depths
    # Customize wired → the guided-wizard Customize button is enabled.
    assert section.customize is ticket._open_panel
    # Direct-lane section: it stages no draft ops.
    assert section.op_kinds == frozenset()
    assert 1 <= len(section.label) <= 80


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def test_embed_names_tickets_and_shows_required_role():
    embed = ticket.build_ticket_setup_embed()
    blob = ((embed.title or "") + (embed.description or "")).lower()
    assert "ticket" in blob
    selected = next(
        (f for f in embed.fields if f.name in ("Selected", "Current")), None
    )
    assert selected is not None
    # No staff role yet → flagged required.
    assert "required" in selected.value.lower()


def test_embed_renders_selected_role_and_log():
    guild = MagicMock()
    guild.get_role.return_value = SimpleNamespace(mention="@Staff")
    log = MagicMock(spec=discord.TextChannel)
    log.mention = "#tickets-log"
    guild.get_channel.return_value = log
    with patch.object(
        ticket.resources, "resolve_role", return_value=SimpleNamespace(mention="@Staff")
    ):
        embed = ticket.build_ticket_setup_embed(
            staff_role_id=10, log_channel_id=20, guild=guild
        )
    field = next(f for f in embed.fields if f.name in ("Selected", "Current"))
    assert "@Staff" in field.value
    assert "#tickets-log" in field.value


# ---------------------------------------------------------------------------
# _open_panel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_panel_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    await ticket._open_panel(interaction, None)
    interaction.response.send_message.assert_awaited_once()
    assert "server" in interaction.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_open_panel_opens_config_view_in_guild():
    interaction = _interaction()
    with patch(
        "views.setup.sections.ticket.ticket_service.get_config",
        new_callable=AsyncMock,
        return_value=None,
    ):
        await ticket.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs["view"], ticket.TicketSetupSectionView)
    assert "Tickets" in (kwargs["embed"].title or "")


# ---------------------------------------------------------------------------
# Enable button — the audited direct-lane write
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enable_refuses_without_staff_role():
    view = ticket.TicketSetupSectionView(SimpleNamespace(id=99))
    interaction = _interaction()
    with patch(
        "views.setup.sections.ticket.ticket_mutation.update_config",
        new_callable=AsyncMock,
    ) as update_mock:
        await _enable_button(view).callback(interaction)
    update_mock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    assert "staff role" in interaction.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_enable_writes_through_audited_update_config():
    view = ticket.TicketSetupSectionView(
        SimpleNamespace(id=99), staff_role_id=555, log_channel_id=777
    )
    interaction = _interaction()
    with (
        patch(
            "views.setup.sections.ticket.ticket_mutation.update_config",
            new_callable=AsyncMock,
        ) as update_mock,
        patch(
            "views.setup.sections.ticket.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await _enable_button(view).callback(interaction)
    update_mock.assert_awaited_once()
    kwargs = update_mock.await_args.kwargs
    assert kwargs["enabled"] is True
    assert kwargs["staff_role_id"] == 555
    assert kwargs["log_channel_id"] == 777
    # actor + guild are positional
    assert update_mock.await_args.args == (1, 99)
    interaction.response.edit_message.assert_awaited_once()
    mark_mock.assert_awaited_once()
