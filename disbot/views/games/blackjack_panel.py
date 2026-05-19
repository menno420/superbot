"""Blackjack hub panel — Phase 7 Option A (router only).

A discovery surface that lists Classic and Rules under the Games hub.
Game logic, modes, replay, and economy paths are **untouched** — every
button either swaps the embed in place or routes back to a parent hub
via the standard ``attach_back_to_*`` factories.

Phase 7 Option A explicitly defers Practice / Replay / Best-of variants
to a follow-up (Phase 7b) once the engine-side design call is made
(``bet=0`` vs separate no-economy path, post-game callback shape,
double-charge prevention).
"""

from __future__ import annotations

import discord

from utils.ui_constants import GAME_COLOR
from views.base import HubView


def build_blackjack_overview_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🃏 Blackjack",
        description=(
            "Classic 21 — solo against the bot, PvP against another "
            "player, or scheduled tournaments. The buttons below explain "
            "how to start each mode; typed shortcuts still work."
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Modes",
        value=(
            "▶ **Classic** — start a standard game\n"
            "📖 **Rules** — how the deal/hit/stand flow works"
        ),
        inline=False,
    )
    embed.set_footer(text="Typed shortcuts: !blackjack, !bj, !bjtournament.")
    return embed


def build_blackjack_classic_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🃏 Blackjack — Classic",
        description=(
            "Start a Classic game with a typed command. Bets are in "
            "🪙 coins; use `0` for a free game."
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Solo vs bot",
        value="`!blackjack <bet>` or `!bj <bet>`",
        inline=False,
    )
    embed.add_field(
        name="PvP challenge",
        value="`!blackjack @user <bet>`",
        inline=False,
    )
    embed.add_field(
        name="Tournament",
        value="`!bjtournament` — open registration",
        inline=False,
    )
    embed.set_footer(text="Click ◀ Overview to return to the Blackjack hub.")
    return embed


def build_blackjack_rules_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🃏 Blackjack — Rules",
        description=(
            "Each player is dealt two cards; the goal is to reach a "
            "hand value as close to 21 as possible without going over."
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Card values",
        value=(
            "• Number cards = face value (2–10)\n"
            "• Face cards (J/Q/K) = 10\n"
            "• Ace = 1 or 11, whichever is best for the hand"
        ),
        inline=False,
    )
    embed.add_field(
        name="Actions",
        value=(
            "• **Hit** — draw another card\n"
            "• **Stand** — keep the current hand\n"
            "• Bust at >21 — the other side wins automatically"
        ),
        inline=False,
    )
    embed.add_field(
        name="Outcomes",
        value=(
            "• Player blackjack (A + 10-value, two cards) usually pays "
            "extra\n"
            "• Tie returns the bet"
        ),
        inline=False,
    )
    embed.set_footer(text="Click ◀ Overview to return to the Blackjack hub.")
    return embed


class BlackjackPanelView(HubView):
    """Router-only Blackjack hub surfaced via Help → Blackjack and the Games hub.

    No game logic. No economy hooks. No new betting modes. The view's
    sole job is to keep Blackjack discoverable from a single panel and
    route to the existing typed commands for the actual start path.
    """

    SUBSYSTEM = "blackjack"

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)

    @discord.ui.button(
        label="▶ Classic",
        style=discord.ButtonStyle.success,
        custom_id="blackjack_panel:classic",
        row=0,
    )
    async def btn_classic(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_blackjack_classic_embed(),
            view=self,
        )

    @discord.ui.button(
        label="📖 Rules",
        style=discord.ButtonStyle.secondary,
        custom_id="blackjack_panel:rules",
        row=0,
    )
    async def btn_rules(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_blackjack_rules_embed(),
            view=self,
        )

    @discord.ui.button(
        label="◀ Overview",
        style=discord.ButtonStyle.secondary,
        custom_id="blackjack_panel:overview",
        row=0,
    )
    async def btn_overview(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_blackjack_overview_embed(),
            view=self,
        )
