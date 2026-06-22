"""Casino hub — the navigation surface under the Games hub.

A router-style panel that groups the casino's group games.  v1 ships **Texas
Hold'em poker** (the multiplayer per-player-ephemeral table); roulette and other
games dock in here as they're built on the same table framework.
"""

from __future__ import annotations

import logging

import discord

from utils.ui_constants import GAME_COLOR
from views.base import HubView
from views.casino import poker_table

logger = logging.getLogger("bot.views.casino.hub")

SUBSYSTEM = "casino"


def build_casino_hub_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎰 Casino",
        description=(
            "Group casino games you play together at one table — everyone gets "
            "their **own private, live-updating hand**.\n\n"
            "Pick a game below. Typed shortcut: `!poker`."
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="🃏 Texas Hold'em Poker",
        value=(
            "Multiplayer poker, 2–8 players. Take a seat, get a private hand, and "
            "bet it out — your cards update live as everyone plays. Play-chips."
        ),
        inline=False,
    )
    embed.add_field(
        name="🎡 Roulette",
        value="_Coming soon — built on the same shared-table framework._",
        inline=False,
    )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


class CasinoHubView(HubView):
    """Router hub for casino games (Games-hub child)."""

    SUBSYSTEM = SUBSYSTEM

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)

    @discord.ui.button(
        label="New Poker Table",
        style=discord.ButtonStyle.success,
        emoji="🃏",
    )
    async def new_poker(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        channel = interaction.channel
        if channel is None or not hasattr(channel, "send"):
            await interaction.response.send_message(
                "Poker tables can only be opened in a server text channel.",
                ephemeral=True,
            )
            return
        existing = poker_table.get_table(interaction.channel_id or 0)
        if existing is not None and not existing.ended:
            await interaction.response.send_message(
                "There's already an active poker table in this channel — "
                "join that one (scroll up) or wait for it to finish.",
                ephemeral=True,
            )
            return
        table = await poker_table.launch_table(
            interaction.client,
            channel,  # type: ignore[arg-type]
            interaction.channel_id or 0,
            interaction.user,
        )
        if table is None:
            await interaction.response.send_message(
                "A poker table is already open here.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "♠ Your poker table is open below — press **Join** to seat players, "
            "then **Start**.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Roulette (soon)",
        style=discord.ButtonStyle.secondary,
        emoji="🎡",
        disabled=True,
    )
    async def roulette(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:  # pragma: no cover - disabled placeholder
        await interaction.response.send_message(
            "Roulette is coming soon!",
            ephemeral=True,
        )


def build_casino_hub_panel(
    author: discord.Member | discord.User,
) -> tuple[discord.Embed, CasinoHubView]:
    """Single source of truth for opening the Casino hub."""
    return build_casino_hub_embed(), CasinoHubView(author)
