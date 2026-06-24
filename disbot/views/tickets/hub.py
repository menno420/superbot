"""Ticket hub panel — the ``!ticket`` / Help-menu entry point.

An ephemeral, author-locked :class:`HubView` summarising the guild's ticket
setup and offering the common actions: open a ticket, list your open tickets,
and (staff only) post the public launcher panel into the current channel.
"""

from __future__ import annotations

import discord

from core.runtime import guild_resources
from services import ticket_service
from views.base import HubView
from views.tickets._shared import TicketOpenModal, is_ticket_staff
from views.tickets.launcher import post_launcher


async def _build_hub_embed(
    guild: discord.Guild,
    user: discord.Member,
) -> discord.Embed:
    cfg = await ticket_service.get_config(guild.id)
    embed = discord.Embed(
        title="🎫 Support tickets",
        color=discord.Color.blurple(),
    )
    if cfg is None or not cfg.is_set_up:
        embed.description = (
            "The ticket system isn't set up yet.\n"
            "An admin can run **`!ticketsetup @StaffRole`** to enable it."
        )
        return embed

    staff = (
        guild_resources.resolve_role(guild, role_id=cfg.staff_role_id)
        if cfg.staff_role_id
        else None
    )
    log = guild.get_channel(cfg.log_channel_id) if cfg.log_channel_id else None
    mine = await ticket_service.list_user_open(guild.id, user.id)
    embed.description = (
        "Open a private support ticket and the staff team will help you out."
    )
    embed.add_field(
        name="Staff role",
        value=staff.mention if staff else "—",
        inline=True,
    )
    embed.add_field(
        name="Transcript log",
        value=log.mention if isinstance(log, discord.TextChannel) else "—",
        inline=True,
    )
    embed.add_field(
        name="Your open tickets",
        value=f"{len(mine)} / {cfg.max_open_per_user}",
        inline=True,
    )
    return embed


class TicketHubView(HubView):
    """Open / list / (staff) post-panel actions."""

    SUBSYSTEM = "ticket"

    def __init__(self, guild: discord.Guild, author: discord.Member) -> None:
        super().__init__(author)
        self._guild = guild

    @discord.ui.button(
        label="Open a ticket",
        emoji="🎫",
        style=discord.ButtonStyle.primary,
    )
    async def open_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        await interaction.response.send_modal(TicketOpenModal(source="command"))

    @discord.ui.button(
        label="My open tickets",
        emoji="📋",
        style=discord.ButtonStyle.secondary,
    )
    async def list_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        mine = await ticket_service.list_user_open(self._guild.id, interaction.user.id)
        if not mine:
            await interaction.response.send_message(
                "You have no open tickets.",
                ephemeral=True,
            )
            return
        lines = [f"• <#{t['channel_id']}> — {t['subject']}" for t in mine]
        await interaction.response.send_message(
            "**Your open tickets:**\n" + "\n".join(lines),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Post panel here",
        emoji="📮",
        style=discord.ButtonStyle.secondary,
    )
    async def post_panel_btn(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        cfg = await ticket_service.get_config(self._guild.id)
        if not is_ticket_staff(interaction.user, cfg):  # type: ignore[arg-type]
            await interaction.response.send_message(
                "Only staff can post the ticket panel.",
                ephemeral=True,
            )
            return
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "Run this in a text channel.",
                ephemeral=True,
            )
            return
        await post_launcher(interaction.channel)
        await interaction.response.send_message(
            "📮 Posted the ticket panel here.",
            ephemeral=True,
        )


async def open_ticket_hub(
    author: discord.Member,
    guild: discord.Guild,
) -> tuple[discord.Embed, TicketHubView]:
    """Build the ticket hub embed + view (Help hook + ``!ticket``)."""
    embed = await _build_hub_embed(guild, author)
    return embed, TicketHubView(guild, author)
