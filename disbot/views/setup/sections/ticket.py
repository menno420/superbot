"""Support-tickets section — opens the ticket config panel inside the wizard.

Tickets were reachable only via ``!help`` → Community hub or the standalone
``!ticketsetup`` command — invisible to a new owner running the ``!setup``
wizard (the surface they actually start from). This section closes that
discoverability gap: tickets appear as a wizard step / ``/setup-hub`` button.

The interactive UI itself lives in the ticket domain
(:mod:`views.tickets.config_panel`) so the wizard and the ``!ticketsetup``
command share one fully button/dropdown-driven panel. This section is the thin
wizard adapter: it opens that panel and marks setup progress. All writes go
through the audited ``ticket_mutation`` direct lane (ticket config is its own
table, not the ``set_setting`` pipeline), so this section stages no draft op —
like the ``suggestions`` / ``server_scan`` sections.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_session
from services.setup_sections import REGISTRY, SetupSection
from views.tickets import open_ticket_config_panel

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.ticket")

SLUG = "ticket"


async def _open_panel(
    interaction: discord.Interaction,
    hub: SetupHubView | None,
) -> None:
    """Open the shared ticket config panel (hub button + wizard Customize)."""
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This can only be used in a server.",
            ephemeral=True,
        )
        return
    embed, view = await open_ticket_config_panel(interaction.user, guild=guild)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:  # pragma: no cover — progress marker is best-effort
        logger.exception("ticket section: mark_in_progress failed")


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    """Section entry — open the ticket config panel."""
    await _open_panel(interaction, hub)


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Support Tickets",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="🎫",
        order=72,
        op_kinds=frozenset(),
        description_if_skipped=(
            "Tickets stay disabled — members can't open private support tickets "
            "until you enable them here or run `!ticketsetup`."
        ),
        depths=frozenset({"standard", "advanced"}),
        customize=_open_panel,
    ),
)


__all__ = ["SLUG", "run"]
