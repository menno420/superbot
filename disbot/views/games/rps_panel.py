"""RPS hub panel — Phase 7 Option A (router only).

Routes from the Games hub into the existing typed RPS flow. The view
contains zero engine logic; every button swaps the embed in place,
listing the typed commands users invoke to actually play.

Phase 7 Option A defers Best-of/Replay variants to a later PR. The
Tournament button routes to the existing tournament-registration flow
(``!rpsregister``) — tournament state lives in ``RPSTournamentCog`` and
is **not** duplicated here.
"""

from __future__ import annotations

import discord

from utils.ui_constants import GAME_COLOR
from views.base import HubView


def build_rps_overview_embed() -> discord.Embed:
    embed = discord.Embed(
        title="✂️ Rock Paper Scissors",
        description=(
            "Quick matches vs the bot or another player, plus scheduled "
            "tournaments with optional entry fees. Pick a mode to see "
            "how to start it."
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Modes",
        value=(
            "▶ **Single Round** — quick match (solo or PvP)\n"
            "🏆 **Tournament** — registration + bracket\n"
            "📖 **Rules** — how the matches work"
        ),
        inline=False,
    )
    embed.set_footer(
        text="Typed shortcuts: !rps, !rpsregister, !rpsstart, !rpshelp.",
    )
    return embed


def build_rps_single_round_embed() -> discord.Embed:
    embed = discord.Embed(
        title="✂️ RPS — Single Round",
        description=(
            "Each round is a single classic Rock Paper Scissors throw "
            "(the underlying tournament cog defaults to best-of-3 for "
            "tournament brackets — single-round behaviour is unchanged "
            "by this panel)."
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Solo vs bot",
        value="`!rps`",
        inline=False,
    )
    embed.add_field(
        name="Challenge a user",
        value="`!rps @user`",
        inline=False,
    )
    embed.add_field(
        name="Stakes match",
        value="`!rps @user <bet>` — both sides cover the bet from 🪙 coins",
        inline=False,
    )
    embed.set_footer(text="Click ◀ Overview to return to the RPS hub.")
    return embed


def build_rps_tournament_embed() -> discord.Embed:
    embed = discord.Embed(
        title="✂️ RPS — Tournament",
        description=(
            "Open a registration window, accept entries via reaction, "
            "then run the bracket. Tournament state and pot accounting "
            "live in `RPSTournamentCog` — this panel does not duplicate "
            "either."
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Open registration",
        value="`!rpsregister` — optionally with a role mention + entry fee",
        inline=False,
    )
    embed.add_field(
        name="Begin bracket",
        value="`!rpsstart` — runs every match in order",
        inline=False,
    )
    embed.add_field(
        name="Help / settings",
        value="`!rpshelp` · `!rpssettings`",
        inline=False,
    )
    embed.set_footer(text="Click ◀ Overview to return to the RPS hub.")
    return embed


def build_rps_rules_embed() -> discord.Embed:
    embed = discord.Embed(
        title="✂️ RPS — Rules",
        description=(
            "Rock crushes Scissors, Scissors cut Paper, Paper covers "
            "Rock. Identical throws are a draw and (in single-round) "
            "stay scoreless; tournaments replay drawn rounds."
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Best-of",
        value=(
            "Tournament matches default to best-of-3 with a configurable "
            "round count via `!rpssettings`."
        ),
        inline=False,
    )
    embed.add_field(
        name="Stakes",
        value=(
            "Stakes matches (`!rps @user <bet>`) debit both sides at "
            "match start; the winner takes the combined pot."
        ),
        inline=False,
    )
    embed.set_footer(text="Click ◀ Overview to return to the RPS hub.")
    return embed


class RPSPanelView(HubView):
    """Router-only RPS hub.

    No tournament state, no match orchestration, no replay logic.
    """

    SUBSYSTEM = "rps_tournament"

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)

    @discord.ui.button(
        label="▶ Single Round",
        style=discord.ButtonStyle.success,
        custom_id="rps_panel:single",
        row=0,
    )
    async def btn_single(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_rps_single_round_embed(),
            view=self,
        )

    @discord.ui.button(
        label="🏆 Tournament",
        style=discord.ButtonStyle.primary,
        custom_id="rps_panel:tournament",
        row=0,
    )
    async def btn_tournament(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_rps_tournament_embed(),
            view=self,
        )

    @discord.ui.button(
        label="📖 Rules",
        style=discord.ButtonStyle.secondary,
        custom_id="rps_panel:rules",
        row=0,
    )
    async def btn_rules(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_rps_rules_embed(),
            view=self,
        )

    @discord.ui.button(
        label="◀ Overview",
        style=discord.ButtonStyle.secondary,
        custom_id="rps_panel:overview",
        row=1,
    )
    async def btn_overview(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_rps_overview_embed(),
            view=self,
        )
