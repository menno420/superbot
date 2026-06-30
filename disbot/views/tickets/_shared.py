"""Shared ticket-view helpers: the open modal, authority check, embeds.

Views may import services (the open path runs through
:mod:`services.ticket_mutation`); they must never import cogs.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer
from services import ticket_mutation, ticket_service

logger = logging.getLogger("bot.views.tickets")

_TICKET_COLOR = discord.Color.blurple()


def is_ticket_staff(
    member: discord.Member,
    cfg: ticket_service.TicketConfig | None,
) -> bool:
    """True if ``member`` may manage tickets (platform owner / admin / manage-guild / staff role)."""
    from config import is_platform_owner

    if is_platform_owner(getattr(member, "id", None)):
        return True
    perms = getattr(member, "guild_permissions", None)
    if perms is not None and (perms.administrator or perms.manage_guild):
        return True
    if cfg is not None and cfg.staff_role_id is not None:
        return any(r.id == cfg.staff_role_id for r in getattr(member, "roles", []))
    return False


def build_launcher_embed(guild_name: str) -> discord.Embed:
    """The public "open a ticket" panel embed."""
    return discord.Embed(
        title="🎫 Support tickets",
        description=(
            "Need help? Click **Open a ticket** below and describe your issue. "
            "A private channel will be created for you and the staff team.\n\n"
            "You can also just **ask me in plain English** (e.g. *“open a ticket, "
            "I need help with …”*) in any channel where I'm listening."
        ),
        color=_TICKET_COLOR,
    ).set_footer(text=guild_name)


def build_welcome_embed(
    ticket_id: int,
    opener_mention: str,
    subject: str,
) -> discord.Embed:
    """The first message posted inside a freshly-opened ticket channel."""
    embed = discord.Embed(
        title=f"🎫 Ticket #{ticket_id}",
        description=(
            f"Thanks {opener_mention} — a staff member will be with you shortly.\n\n"
            f"**Subject:** {subject}\n\n"
            "Describe your issue in as much detail as you can. Staff can "
            "**Claim** this ticket and **Close** it when it's resolved."
        ),
        color=_TICKET_COLOR,
    )
    embed.set_footer(text="Use the buttons below to manage this ticket.")
    return embed


class TicketOpenModal(discord.ui.Modal, title="Open a support ticket"):
    """Collects the subject, then opens the ticket via the audited service."""

    subject: discord.ui.TextInput = discord.ui.TextInput(  # type: ignore[type-arg]
        label="What do you need help with?",
        placeholder="Briefly describe your issue…",
        style=discord.TextStyle.paragraph,
        max_length=200,
        required=True,
    )

    def __init__(self, *, source: str = "panel") -> None:
        super().__init__()
        self._source = source

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or not isinstance(
            interaction.user,
            discord.Member,
        ):
            await interaction.response.send_message(
                "Tickets can only be opened inside a server.",
                ephemeral=True,
            )
            return
        if not await safe_defer(interaction, ephemeral=True, thinking=True):
            return
        result = await ticket_mutation.open_ticket(
            interaction.guild,
            interaction.user,
            str(self.subject.value),
            source=self._source,
        )
        await interaction.followup.send(result.message, ephemeral=True)
