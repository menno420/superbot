"""The public ticket launcher panel — a persistent "Open a ticket" button.

Anchor-free :class:`PersistentView` (the ``SetupLauncherView`` /
``UxLabPersistentDemo`` precedent): one static custom_id, registered once at
boot via ``bot.add_view`` so the button keeps working across restarts for
*every* member (the base ownership check is a no-op when there's no anchor
row, which is what we want — this panel is public).
"""

from __future__ import annotations

import discord

from core.runtime.persistent_views import PersistentView, register
from views.tickets._shared import TicketOpenModal, build_launcher_embed


@register
class TicketLauncherView(PersistentView):
    """A single public button that opens the ticket modal."""

    SUBSYSTEM = "ticket"
    PANEL_ID = "ticket_launcher"
    # Public, single-purpose launcher — opts out of the Help / Back-to-hub
    # auto-nav (it lives in a public channel for non-staff members).
    STANDARD_NAV = False

    @discord.ui.button(
        label="Open a ticket",
        style=discord.ButtonStyle.primary,
        emoji="🎫",
        custom_id="ticket:launcher:open",
    )
    async def open_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        await interaction.response.send_modal(TicketOpenModal(source="panel"))


async def post_launcher(channel: discord.TextChannel) -> discord.Message:
    """Post the launcher panel into ``channel``; return the sent message."""
    embed = build_launcher_embed(channel.guild.name)
    return await channel.send(embed=embed, view=TicketLauncherView())
