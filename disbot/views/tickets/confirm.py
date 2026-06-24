"""AI ticket-open confirmation — the one-click [Open ticket]/[Cancel] prompt.

Posted by ``cogs.ticket_cog`` when the read-only AI tool ``open_support_ticket``
asks (via the ``ticket.open_requested`` event) to open a ticket on the user's
behalf. The user confirms with a click; only then does the audited
``ticket_mutation.open_ticket`` run. This keeps the natural-language path on the
"mutations flow through a deterministic service after explicit confirmation"
contract — the AI proposes, the human commits.

Locked to the requesting user (``BaseView`` invoker check). Transient (a short
timeout); a missed window just means the user asks again — no persistence.
"""

from __future__ import annotations

import discord

from services import ticket_mutation
from views.base import BaseView


class TicketConfirmView(BaseView):
    """[Open ticket] / [Cancel] for an AI-proposed ticket."""

    # A transient confirmation prompt, not a navigable panel.
    STANDARD_NAV = False

    def __init__(self, requester: discord.Member, subject: str) -> None:
        super().__init__(requester, timeout=120)
        self._requester = requester
        self._subject = subject

    @discord.ui.button(
        label="Open ticket",
        emoji="🎫",
        style=discord.ButtonStyle.success,
    )
    async def open(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        if interaction.guild is None or not isinstance(
            interaction.user,
            discord.Member,
        ):
            await interaction.response.send_message(
                "Tickets can only be opened inside a server.",
                ephemeral=True,
            )
            return
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content="🎫 Opening your ticket…",
            view=self,
        )
        result = await ticket_mutation.open_ticket(
            interaction.guild,
            interaction.user,
            self._subject,
            source="ai",
        )
        await interaction.followup.send(result.message, ephemeral=True)

    @discord.ui.button(label="Cancel", emoji="✖️", style=discord.ButtonStyle.secondary)
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content="Okay — no ticket opened.",
            view=self,
        )


def build_confirm_embed(subject: str) -> discord.Embed:
    """The embed shown above the confirm buttons."""
    return discord.Embed(
        title="🎫 Open a support ticket?",
        description=(
            f"I can open a private support ticket for this:\n\n> {subject}\n\n"
            "Click **Open ticket** to create it, or **Cancel**."
        ),
        color=discord.Color.blurple(),
    )
