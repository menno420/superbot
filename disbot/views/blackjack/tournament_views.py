"""Blackjack tournament views + round orchestration (S4.5).

Three pieces:

  _TournRegistrationView  — the persistent "Join" button on the
                            registration message
  _TournBlackjackView     — one-view-per-round-per-player game view
  _start_tourn_round      — deals a fresh hand for one player's round
  _check_tourn_done       — runs when every player has finished;
                            ranks results, pays out the pot, cleans up
                            channels, drops persisted entries.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import resources
from services import game_wager_workflow, tournament_state_service
from services.blackjack_engine import hand_value as _hand_value
from services.blackjack_engine import is_blackjack as _is_blackjack
from services.blackjack_state import (
    BLACKJACK_TOURNAMENT_SUBSYSTEM,
    TOURN_BET_PER_ROUND,
    _active,
    _BjTournament,
    _Game,
    _tournaments,
    _TournPlayerState,
)
from utils.channels import cleanup_category
from utils.ui_constants import ECONOMY_COLOR, ERROR_COLOR, GAME_COLOR, SUCCESS_COLOR
from views.base import handle_view_error as _on_view_error
from views.blackjack.embeds import _game_embed, _update_tourn_embed

logger = logging.getLogger("bot")


class _TournRegistrationView(discord.ui.View):
    def __init__(self, tournament: _BjTournament):
        super().__init__(timeout=tournament.duration_mins * 60 + 10)
        self.tourn = tournament

    @discord.ui.button(
        label="Join Tournament",
        style=discord.ButtonStyle.green,
        emoji="🃏",
    )
    async def join_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        ok, msg = await self.tourn.try_join(interaction.user.id)
        await interaction.response.send_message(msg, ephemeral=True)
        if ok:
            await _update_tourn_embed(self.tourn)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        await _on_view_error(self, interaction, error, item)


class _TournBlackjackView(discord.ui.View):
    """One view per round per player in a tournament."""

    def __init__(
        self,
        game: _Game,
        player_state: _TournPlayerState,
        channel: discord.TextChannel,
        tourn: _BjTournament,
        bot: commands.Bot,
    ):
        super().__init__(timeout=120)
        self.game = game
        self.ps = player_state
        self.channel = channel
        self.tourn = tourn
        self.bot = bot
        self.message: discord.Message | None = None

    async def _finish_round(
        self,
        interaction: discord.Interaction,
        result: str,
        color: discord.Color,
        chip_delta: int,
        reveal: bool = True,
    ):
        _active.pop((self.game.user_id, self.game.guild_id), None)
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]

        self.ps.chips = max(0, self.ps.chips + chip_delta)
        embed = _game_embed(self.game, reveal=reveal)
        embed.color = color
        embed.add_field(
            name=result,
            value=f"Chips: **{self.ps.chips}** | Rounds left: **{self.ps.rounds_left - 1}**",
            inline=False,
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
        self.ps.rounds_left -= 1

        if self.ps.chips == 0 or self.ps.rounds_left == 0:
            self.ps.done = True
            self.tourn.results[self.ps.user_id] = self.ps.chips
            await self.channel.send(
                f"✅ You finished the tournament with **{self.ps.chips}** chips!",
            )
            await _check_tourn_done(self.tourn, self.bot)
        else:
            await _start_tourn_round(self.ps, self.channel, self.tourn, self.bot)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message("Not your game.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        _active.pop((self.game.user_id, self.game.guild_id), None)
        self.ps.chips = max(0, self.ps.chips - TOURN_BET_PER_ROUND)
        self.ps.rounds_left -= 1
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            await self.message.edit(content="⏰ Timed out — hand forfeited.", view=self)
        except Exception:
            pass
        if self.ps.chips == 0 or self.ps.rounds_left == 0:
            self.ps.done = True
            self.tourn.results[self.ps.user_id] = self.ps.chips
            await _check_tourn_done(self.tourn, self.bot)
        else:
            await _start_tourn_round(self.ps, self.channel, self.tourn, self.bot)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        await _on_view_error(self, interaction, error, item)

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green, emoji="👊")
    async def hit(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.game.hit()
        if _hand_value(self.game.player) > 21:
            await self._finish_round(
                interaction,
                "💥 Bust!",
                ERROR_COLOR,
                -TOURN_BET_PER_ROUND,
            )
            return
        await interaction.response.edit_message(embed=_game_embed(self.game), view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.grey, emoji="✋")
    async def stand(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._resolve(interaction)

    async def _resolve(self, interaction: discord.Interaction):
        self.game.dealer_play()
        pv = _hand_value(self.game.player)
        dv = _hand_value(self.game.dealer)
        bet = TOURN_BET_PER_ROUND

        if _is_blackjack(self.game.player):
            await self._finish_round(
                interaction,
                "🎉 Blackjack!",
                ECONOMY_COLOR,
                int(bet * 1.5),
            )
        elif dv > 21:
            await self._finish_round(
                interaction,
                "🎉 Dealer busts!",
                SUCCESS_COLOR,
                bet,
            )
        elif pv > dv:
            await self._finish_round(interaction, "🎉 You win!", SUCCESS_COLOR, bet)
        elif pv == dv:
            await self._finish_round(interaction, "🤝 Push.", GAME_COLOR, 0)
        else:
            await self._finish_round(interaction, "😞 Dealer wins.", ERROR_COLOR, -bet)


async def _start_tourn_round(
    ps: _TournPlayerState,
    channel: discord.TextChannel,
    tourn: _BjTournament,
    bot: commands.Bot,
):
    game = _Game(
        ps.user_id,
        ps.guild_id,
        0,
        tournament_chips=ps.chips,
        channel_id=channel.id,
    )
    _active[(ps.user_id, ps.guild_id)] = game
    member = resources.resolve_member(channel.guild, ps.user_id)
    mention = member.mention if member else f"<@{ps.user_id}>"

    embed = _game_embed(
        game,
        title=f"🃏 Round {tourn.rounds - ps.rounds_left + 1}/{tourn.rounds}",
    )
    view = _TournBlackjackView(game, ps, channel, tourn, bot)
    msg = await channel.send(content=mention, embed=embed, view=view)
    view.message = msg


async def _check_tourn_done(tourn: _BjTournament, bot: commands.Bot):
    if len(tourn.results) < len(tourn.players):
        return  # not all players finished

    # Settle-once: two players finishing concurrently (or a timeout racing the
    # last hand) each reach here past the all-finished check; claim before any
    # await so exactly one caller runs the payout. The paid path is already
    # row-consumption idempotent, but the FREE-tournament reward leg has no
    # escrow rows to consume — this claim is its only double-pay guard.
    if not tourn.claim_settlement():
        return

    announce = bot.get_channel(tourn.announce_id)
    guild = bot.get_guild(tourn.guild_id)

    # Rank players
    ranking = sorted(tourn.results.items(), key=lambda x: x[1], reverse=True)
    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, chips) in enumerate(ranking):
        icon = medals[i] if i < 3 else f"#{i + 1}"
        name = resources.member_display(guild, uid) if guild else f"<@{uid}>"
        lines.append(f"{icon} **{name}** — {chips} chips")

    winner_id = ranking[0][0] if ranking else None

    embed = discord.Embed(
        title="🏆 Blackjack Tournament Results",
        description="\n".join(lines),
        color=ECONOMY_COLOR,
    )
    # P0-1 — pay the winner the escrowed pot (the sum of the actual entry
    # rows) and release those rows in ONE idempotent transaction.  This
    # replaces the credit-then-separate-clear pair: a re-run finds no
    # rows and cannot double-pay, and recovery cannot refund an
    # already-settled tournament.
    result = await game_wager_workflow.payout_tournament(
        guild_id=tourn.guild_id,
        subsystem=BLACKJACK_TOURNAMENT_SUBSYSTEM,
        winner_id=winner_id,
        reason="blackjack:tournament_win",
        free_reward=200,
        free_reason="blackjack:tournament_free_reward",
    )
    if result.paid and tourn.entry_fee > 0:
        embed.add_field(
            name="Winner's payout",
            value=(
                f"<@{winner_id}> receives **{result.amount}** 🪙 "
                f"(Balance: {result.new_winner_balance} 🪙)"
            ),
            inline=False,
        )
    elif result.paid:
        embed.add_field(
            name="Winner's reward",
            value=(
                f"<@{winner_id}> receives **{result.amount}** 🪙 "
                f"(Balance: {result.new_winner_balance} 🪙)"
            ),
            inline=False,
        )

    if announce:
        await announce.send(embed=embed)  # type: ignore[union-attr]

    # Clean up private channels
    if tourn.category:
        await cleanup_category(tourn.category)

    _tournaments.pop(tourn.guild_id, None)
    await tournament_state_service.clear_active(tourn.guild_id)
