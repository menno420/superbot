"""In-channel ticket control panel — Claim / Close (persistent).

Posted into each ticket channel (by ``cogs.ticket_cog`` on the ``ticket.opened``
event). Anchor-free + static custom_ids so the buttons survive restarts. The
panel is reachable by everyone in the channel, so each callback re-checks
authority at press time (the capability-authority panel rule): claiming and
closing require staff (the configured staff role, or manage-guild/admin); the
opener may also close their own ticket.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.persistent_views import PersistentView, register
from services import ticket_mutation, ticket_service
from views.tickets._shared import is_ticket_staff

logger = logging.getLogger("bot.views.tickets")


class TicketCloseModal(discord.ui.Modal, title="Close ticket"):
    """Optional close reason; submitting confirms the close."""

    reason: discord.ui.TextInput = discord.ui.TextInput(  # type: ignore[type-arg]
        label="Reason (optional)",
        placeholder="Why is this ticket being closed?",
        style=discord.TextStyle.paragraph,
        max_length=400,
        required=False,
    )

    def __init__(self, ticket: dict) -> None:
        super().__init__()
        self._ticket = ticket

    async def on_submit(self, interaction: discord.Interaction) -> None:
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel) or not isinstance(
            interaction.user,
            discord.Member,
        ):
            await interaction.response.send_message(
                "This isn't a ticket channel.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "🔒 Closing this ticket…",
            ephemeral=True,
        )
        await ticket_mutation.close_ticket(
            channel,
            self._ticket,
            interaction.user,
            reason=str(self.reason.value) or None,
        )


@register
class TicketControlView(PersistentView):
    """Claim + Close buttons inside a ticket channel."""

    SUBSYSTEM = "ticket"
    PANEL_ID = "ticket_control"
    STANDARD_NAV = False

    async def _resolve(
        self,
        interaction: discord.Interaction,
    ) -> tuple[dict, ticket_service.TicketConfig | None] | None:
        """Return ``(ticket_row, config)`` or ``None`` (with an error reply)."""
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "This isn't a ticket channel.",
                ephemeral=True,
            )
            return None
        ticket = await ticket_service.get_ticket_for_channel(channel.id)
        if ticket is None or ticket.get("status") != "open":
            await interaction.response.send_message(
                "There's no open ticket bound to this channel.",
                ephemeral=True,
            )
            return None
        cfg = await ticket_service.get_config(channel.guild.id)
        return ticket, cfg

    @discord.ui.button(
        label="Claim",
        style=discord.ButtonStyle.success,
        emoji="✋",
        custom_id="ticket:control:claim",
    )
    async def claim(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        resolved = await self._resolve(interaction)
        if resolved is None:
            return
        ticket, cfg = resolved
        if not is_ticket_staff(interaction.user, cfg):  # type: ignore[arg-type]
            await interaction.response.send_message(
                "Only staff can claim tickets.",
                ephemeral=True,
            )
            return
        result = await ticket_mutation.claim_ticket(ticket, interaction.user)  # type: ignore[arg-type]
        await interaction.response.send_message(
            result.message,
            ephemeral=not result.success,
        )

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="ticket:control:close",
    )
    async def close(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        resolved = await self._resolve(interaction)
        if resolved is None:
            return
        ticket, cfg = resolved
        is_opener = interaction.user.id == int(ticket["opener_id"])
        if not (is_opener or is_ticket_staff(interaction.user, cfg)):  # type: ignore[arg-type]
            await interaction.response.send_message(
                "Only staff or the ticket opener can close this ticket.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(TicketCloseModal(ticket))


def build_control_view() -> TicketControlView:
    """Fresh control view for posting into a new ticket channel."""
    return TicketControlView()
