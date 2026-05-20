"""Readiness section — runs the readiness scan and posts the embed.

Extracted from the previous `SetupHubView._readiness` hardcoded button.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_session
from services.setup_sections import REGISTRY, SetupSection

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.readiness")

SLUG = "readiness"


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Readiness requires a guild context.",
            ephemeral=True,
        )
        return

    from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

    embed = await build_setup_readiness_embed(guild.id, guild=guild)
    await interaction.response.send_message(embed=embed, ephemeral=True)

    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("setup hub: mark_in_progress failed")


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Run readiness scan",
        style=discord.ButtonStyle.primary,
        run=run,
        order=10,
    ),
)


__all__ = ["SLUG", "run"]
