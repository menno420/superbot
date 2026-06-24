"""Tests for the support-tickets setup section (thin wizard adapter).

The interactive UI moved to ``views.tickets.config_panel`` (shared with
``!ticketsetup``); this section just registers the wizard button and opens that
panel. Pins: registration metadata, ``customize`` wired (so the guided-wizard
Customize button is enabled), DM rejection, and that opening it sends the shared
``TicketConfigPanelView`` + marks setup progress.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.setup_sections import REGISTRY
from views.setup.sections import ticket
from views.tickets import TicketConfigPanelView


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
async def test_open_panel_sends_config_panel_and_marks_progress():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = SimpleNamespace(id=1, get_channel=lambda _id: None)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    with patch(
        "views.tickets.config_panel.ticket_service.get_config",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "views.setup.sections.ticket.setup_session.mark_in_progress",
        new_callable=AsyncMock,
    ) as mark_mock:
        await ticket.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs["view"], TicketConfigPanelView)
    mark_mock.assert_awaited_once()
