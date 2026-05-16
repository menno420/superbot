from __future__ import annotations

import asyncio
import logging
import random

import discord
from discord.ext import commands

from core.runtime import tasks
from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services import economy_service
from utils import db
from utils.channels import cleanup_category, create_private_channel
from utils.settings_keys import ACTIVE_TOURNAMENT
from utils.tournaments import TournamentRegistration
from utils.ui_constants import ECONOMY_COLOR, ERROR_COLOR, GAME_COLOR, SUCCESS_COLOR

logger = logging.getLogger("bot")


async def _on_view_error(
    view: discord.ui.View,
    interaction: discord.Interaction,
    error: Exception,
    item: discord.ui.Item,  # type: ignore[type-arg]
) -> None:
    logger.error(
        "View error | view=%s item_type=%s custom_id=%r label=%r "
        "user=%s guild=%s channel=%s message=%s",
        type(view).__name__,
        type(item).__name__,
        getattr(item, "custom_id", None),
        getattr(item, "label", None),
        getattr(interaction.user, "id", None),
        interaction.guild_id,
        interaction.channel_id,
        interaction.message.id if interaction.message else None,
        exc_info=error,
    )
    if not interaction.response.is_done():
        try:
            await interaction.response.send_message(
                "An error occurred. Please try again.",
                ephemeral=True,
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Card engine
# ---------------------------------------------------------------------------

SUITS = ("♠", "♥", "♦", "♣")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
FREE_WIN_COINS = 50
TOURN_START_CHIPS = 1000
TOURN_BET_PER_ROUND = 200


def _rank_value(rank: str) -> int:
    if rank in ("J", "Q", "K"):
        return 10
    if rank == "A":
        return 11
    return int(rank)


def _hand_value(hand: list[str]) -> int:
    total = sum(_rank_value(c.split()[0]) for c in hand)
    aces = sum(1 for c in hand if c.startswith("A"))
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def _new_deck() -> list[str]:
    deck = [f"{r} {s}" for r in RANKS for s in SUITS]
    random.shuffle(deck)
    return deck


def _hand_str(hand: list[str], hide_second: bool = False) -> str:
    if hide_second:
        return f"{hand[0]}  ||?||"
    return "  ".join(hand)


def _is_blackjack(hand: list[str]) -> bool:
    return len(hand) == 2 and _hand_value(hand) == 21


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------


class _Game:
    def __init__(
        self,
        user_id: int,
        guild_id: int,
        bet: int,
        tournament_chips: int | None = None,
    ):
        self.user_id = user_id
        self.guild_id = guild_id
        self.bet = bet
        self.doubled = False
        self.tournament_chips = tournament_chips  # None = normal game
        self.deck = _new_deck()
        self.player: list[str] = [self.deck.pop(), self.deck.pop()]
        self.dealer: list[str] = [self.deck.pop(), self.deck.pop()]
        # PvP linkage (set externally)
        self.pvp_peer_id: int | None = None
        self.pvp_state: _PvPState | None = None

    def hit(self) -> str:
        card = self.deck.pop()
        self.player.append(card)
        return card

    def dealer_play(self):
        while _hand_value(self.dealer) < 17:
            self.dealer.append(self.deck.pop())


_active: dict[tuple[int, int], _Game] = {}  # (user_id, guild_id) → game


# ---------------------------------------------------------------------------
# PvP state
# ---------------------------------------------------------------------------


class _PvPState:
    def __init__(self, p1: int, p2: int, guild_id: int, bet: int, channel_id: int):
        self.p1 = p1
        self.p2 = p2
        self.guild_id = guild_id
        self.bet = bet
        self.channel_id = channel_id
        self.results: dict[int, int] = {}  # user_id → final hand value (-1 = bust)
        self.messages: dict[int, discord.Message] = {}


_pvp: dict[frozenset, _PvPState] = {}  # frozenset({p1, p2}) → state


# ---------------------------------------------------------------------------
# Tournament state
# ---------------------------------------------------------------------------


class _BjTournament(TournamentRegistration):
    def __init__(
        self,
        host_id: int,
        guild_id: int,
        announce_id: int,
        entry_fee: int,
        rounds: int,
        duration_mins: int,
    ):
        super().__init__(host_id, guild_id, announce_id, entry_fee, duration_mins)
        self.rounds = rounds
        self.results: dict[int, int] = {}  # user_id → final chips
        self.category: discord.CategoryChannel | None = None


_tournaments: dict[int, _BjTournament] = {}  # guild_id → tournament


# ---------------------------------------------------------------------------
# Embed helpers
# ---------------------------------------------------------------------------


def _game_embed(
    game: _Game,
    reveal: bool = False,
    title: str = "🃏 Blackjack",
) -> discord.Embed:
    pv = _hand_value(game.player)
    if reveal:
        dv = _hand_value(game.dealer)
        d_str = _hand_str(game.dealer)
        d_lbl = f"Dealer ({dv})"
    else:
        d_str = _hand_str(game.dealer, hide_second=True)
        d_lbl = f"Dealer ({_rank_value(game.dealer[0].split()[0])}+?)"

    bet_str = f"**{game.bet}** 🪙" if game.bet else f"Free (win = +{FREE_WIN_COINS} 🪙)"
    if game.tournament_chips is not None:
        bet_str = f"Tournament chips: **{game.tournament_chips}** | Bet: {TOURN_BET_PER_ROUND}"

    embed = discord.Embed(title=title, color=SUCCESS_COLOR)
    embed.add_field(name=d_lbl, value=d_str, inline=False)
    embed.add_field(
        name=f"Your hand ({pv})",
        value=_hand_str(game.player),
        inline=False,
    )
    embed.add_field(name="Bet", value=bet_str, inline=True)
    return embed


# ---------------------------------------------------------------------------
# Solo / PvP game view
# ---------------------------------------------------------------------------


class BlackjackView(discord.ui.View):
    def __init__(self, game: _Game, on_finish=None):
        super().__init__(timeout=120)
        self.game = game
        self.on_finish = on_finish  # async callback(game, outcome_value)
        self.message: discord.Message | None = None
        self.double_btn.disabled = game.bet == 0 or game.tournament_chips is not None

    async def _finish(
        self,
        interaction: discord.Interaction,
        result: str,
        color: discord.Color,
        coin_delta: int,
        hand_value: int,
    ):
        # Idempotent defer — protects the chain hit_btn/stand_btn/double_btn →
        # _resolve → _finish, where balance writes precede the message edit.
        if not await safe_defer(interaction):
            return
        key = (self.game.user_id, self.game.guild_id)
        _active.pop(key, None)
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]

        embed = _game_embed(self.game, reveal=True)
        embed.color = color

        if self.game.tournament_chips is None:
            new_bal = await db.add_coins(
                self.game.user_id,
                self.game.guild_id,
                coin_delta,
            )
            delta_str = f"+{coin_delta}" if coin_delta >= 0 else str(coin_delta)
            embed.add_field(
                name=result,
                value=f"{delta_str} 🪙  |  Balance: **{new_bal}** 🪙",
                inline=False,
            )
        else:
            embed.add_field(name=result, value="​", inline=False)

        await safe_edit(interaction, embed=embed, view=self)
        self.stop()

        if self.on_finish:
            await self.on_finish(self.game, hand_value)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message(
                "This isn't your hand.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        _active.pop((self.game.user_id, self.game.guild_id), None)
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(content="Game timed out.", view=self)
        except Exception:
            pass
        if self.on_finish:
            await self.on_finish(self.game, -1)  # treat as bust on timeout

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        await _on_view_error(self, interaction, error, item)

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green, emoji="👊")
    async def hit_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.game.hit()
        pv = _hand_value(self.game.player)
        if pv > 21:
            effective = self.game.bet * 2 if self.game.doubled else self.game.bet
            await self._finish(
                interaction,
                "💥 Bust — you lose!",
                ERROR_COLOR,
                -effective if effective else 0,
                -1,
            )
            return
        self.double_btn.disabled = True
        await interaction.response.edit_message(embed=_game_embed(self.game), view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.grey, emoji="✋")
    async def stand_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._resolve(interaction)

    @discord.ui.button(
        label="Double Down",
        style=discord.ButtonStyle.blurple,
        emoji="✌️",
    )
    async def double_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        bal = await db.get_coins(self.game.user_id, self.game.guild_id)
        if bal < self.game.bet * 2:
            await safe_followup(
                interaction,
                f"❌ Need {self.game.bet * 2} 🪙 to double (you have {bal}).",
                ephemeral=True,
            )
            return
        self.game.hit()
        self.game.doubled = True
        if _hand_value(self.game.player) > 21:
            await self._finish(
                interaction,
                "💥 Bust — you lose!",
                ERROR_COLOR,
                -(self.game.bet * 2),
                -1,
            )
            return
        await self._resolve(interaction)

    async def _resolve(self, interaction: discord.Interaction):
        self.game.dealer_play()
        pv = _hand_value(self.game.player)
        dv = _hand_value(self.game.dealer)
        effective = self.game.bet * 2 if self.game.doubled else self.game.bet

        if _is_blackjack(self.game.player):
            payout = int(effective * 1.5) if effective else FREE_WIN_COINS
            await self._finish(interaction, "🎉 Blackjack!", ECONOMY_COLOR, payout, pv)
        elif dv > 21:
            payout = effective if effective else FREE_WIN_COINS
            await self._finish(
                interaction,
                "🎉 Dealer busts — you win!",
                SUCCESS_COLOR,
                payout,
                pv,
            )
        elif pv > dv:
            payout = effective if effective else FREE_WIN_COINS
            await self._finish(interaction, "🎉 You win!", SUCCESS_COLOR, payout, pv)
        elif pv == dv:
            await self._finish(interaction, "🤝 Push — tie.", GAME_COLOR, 0, pv)
        else:
            loss = -effective if effective else 0
            await self._finish(interaction, "😞 Dealer wins.", ERROR_COLOR, loss, pv)


# ---------------------------------------------------------------------------
# PvP Challenge
# ---------------------------------------------------------------------------


class _ChallengeView(discord.ui.View):
    def __init__(
        self,
        challenger: discord.Member,
        opponent: discord.Member,
        guild_id: int,
        bet: int,
    ):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.guild_id = guild_id
        self.bet = bet
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message(
                "This challenge isn't for you.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, _: discord.ui.Button):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content="✅ Challenge accepted — dealing hands…",
            view=self,
        )
        self.stop()
        await _start_pvp(
            interaction,
            self.challenger,
            self.opponent,
            self.guild_id,
            self.bet,
        )

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, emoji="❌")
    async def decline(self, interaction: discord.Interaction, _: discord.ui.Button):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content=f"❌ {self.opponent.display_name} declined the challenge.",
            view=self,
        )
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(content="⏰ Challenge timed out.", view=self)
        except Exception:
            pass

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        await _on_view_error(self, interaction, error, item)


async def _start_pvp(
    interaction: discord.Interaction,
    p1: discord.Member,
    p2: discord.Member,
    guild_id: int,
    bet: int,
):
    channel = interaction.channel
    state = _PvPState(p1.id, p2.id, guild_id, bet, channel.id)
    key = frozenset({p1.id, p2.id})
    _pvp[key] = state

    for player in (p1, p2):
        uid = player.id
        gid = guild_id
        game = _Game(uid, gid, bet)
        game.pvp_peer_id = p2.id if uid == p1.id else p1.id
        game.pvp_state = state
        _active[(uid, gid)] = game

        if _is_blackjack(game.player):
            embed = _game_embed(
                game,
                reveal=True,
                title=f"🃏 {player.display_name}'s hand",
            )
            embed.color = ECONOMY_COLOR
            embed.add_field(
                name="Blackjack!",
                value="Waiting for opponent…",
                inline=False,
            )
            msg = await channel.send(content=player.mention, embed=embed)  # type: ignore[union-attr]
            state.messages[uid] = msg
            state.results[uid] = 21
            _active.pop((uid, gid), None)
        else:

            async def _pvp_finish(
                g: _Game,
                hand_val: int,
                _player=player,
                _state=state,
            ):
                _state.results[g.user_id] = hand_val
                if len(_state.results) == 2:
                    await _resolve_pvp(_state, channel)  # type: ignore[arg-type]

            view = BlackjackView(game, on_finish=_pvp_finish)
            embed = _game_embed(game, title=f"🃏 {player.display_name}'s hand")
            msg = await channel.send(content=player.mention, embed=embed, view=view)  # type: ignore[union-attr]
            view.message = msg
            state.messages[uid] = msg

    # If both got instant blackjack
    if len(state.results) == 2:
        await _resolve_pvp(state, channel)  # type: ignore[arg-type]


async def _resolve_pvp(state: _PvPState, channel: discord.TextChannel):
    key = frozenset({state.p1, state.p2})
    _pvp.pop(key, None)

    v1 = state.results.get(state.p1, -1)
    v2 = state.results.get(state.p2, -1)

    if v1 == -1 and v2 == -1:
        result = "🤝 Both busted — tie! No coins exchanged."
        coin_change = 0
        winner_id = None
    elif v1 == -1:
        winner_id = state.p2
        result = f"<@{state.p2}> wins (opponent busted)!"
        coin_change = state.bet
    elif v2 == -1:
        winner_id = state.p1
        result = f"<@{state.p1}> wins (opponent busted)!"
        coin_change = state.bet
    elif v1 > v2:
        winner_id = state.p1
        result = f"<@{state.p1}> wins with **{v1}** vs **{v2}**!"
        coin_change = state.bet
    elif v2 > v1:
        winner_id = state.p2
        result = f"<@{state.p2}> wins with **{v2}** vs **{v1}**!"
        coin_change = state.bet
    else:
        result = f"🤝 Tie — both had **{v1}**. No coins exchanged."
        coin_change = 0
        winner_id = None

    if coin_change and winner_id:
        loser_id = state.p2 if winner_id == state.p1 else state.p1
        payout = coin_change if coin_change else FREE_WIN_COINS
        await db.add_coins(winner_id, state.guild_id, payout)
        await db.add_coins(loser_id, state.guild_id, -payout)

    embed = discord.Embed(
        title="🃏 Blackjack PvP Result",
        description=result,
        color=ECONOMY_COLOR if winner_id else GAME_COLOR,
    )
    embed.add_field(
        name=f"<@{state.p1}>",
        value=f"**{v1 if v1 >= 0 else 'Bust'}**",
        inline=True,
    )
    embed.add_field(
        name=f"<@{state.p2}>",
        value=f"**{v2 if v2 >= 0 else 'Bust'}**",
        inline=True,
    )
    await channel.send(embed=embed)


# ---------------------------------------------------------------------------
# Tournament registration
# ---------------------------------------------------------------------------


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


async def _update_tourn_embed(t: _BjTournament):
    if not t.reg_message:
        return
    embed = _tourn_embed(t)
    try:
        await t.reg_message.edit(embed=embed)
    except Exception:
        pass


def _tourn_embed(t: _BjTournament) -> discord.Embed:
    fee_str = f"**{t.entry_fee}** 🪙" if t.entry_fee else "Free"
    embed = discord.Embed(
        title="🃏 Blackjack Tournament — Registration Open",
        color=SUCCESS_COLOR,
    )
    embed.add_field(name="Entry Fee", value=fee_str, inline=True)
    embed.add_field(name="Rounds", value=str(t.rounds), inline=True)
    embed.add_field(name="Duration", value=f"{t.duration_mins} min", inline=True)
    embed.add_field(name="Players", value=str(len(t.players)), inline=True)
    embed.add_field(name="Pot", value=f"{t.pot} 🪙", inline=True)
    embed.set_footer(text="React ✅ or click Join to register.")
    return embed


# ---------------------------------------------------------------------------
# Tournament play
# ---------------------------------------------------------------------------


class _TournPlayerState:
    def __init__(self, user_id: int, guild_id: int, rounds: int):
        self.user_id = user_id
        self.guild_id = guild_id
        self.chips = TOURN_START_CHIPS
        self.rounds_left = rounds
        self.done = False


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
            item.disabled = True
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
    game = _Game(ps.user_id, ps.guild_id, 0, tournament_chips=ps.chips)
    _active[(ps.user_id, ps.guild_id)] = game
    member = channel.guild.get_member(ps.user_id)
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

    announce = bot.get_channel(tourn.announce_id)
    guild = bot.get_guild(tourn.guild_id)

    # Rank players
    ranking = sorted(tourn.results.items(), key=lambda x: x[1], reverse=True)
    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, chips) in enumerate(ranking):
        icon = medals[i] if i < 3 else f"#{i+1}"
        member = guild.get_member(uid) if guild else None
        name = member.display_name if member else f"<@{uid}>"
        lines.append(f"{icon} **{name}** — {chips} chips")

    winner_id = ranking[0][0] if ranking else None
    pot = tourn.pot

    embed = discord.Embed(
        title="🏆 Blackjack Tournament Results",
        description="\n".join(lines),
        color=ECONOMY_COLOR,
    )
    if winner_id and pot:
        new_bal = await economy_service.credit(
            tourn.guild_id,
            winner_id,
            pot,
            reason="blackjack:tournament_win",
        )
        embed.add_field(
            name="Winner's payout",
            value=f"<@{winner_id}> receives **{pot}** 🪙 (Balance: {new_bal} 🪙)",
            inline=False,
        )
    elif winner_id and not pot:
        reward = 200
        new_bal = await economy_service.credit(
            tourn.guild_id,
            winner_id,
            reward,
            reason="blackjack:tournament_free_reward",
        )
        embed.add_field(
            name="Winner's reward",
            value=f"<@{winner_id}> receives **{reward}** 🪙 (Balance: {new_bal} 🪙)",
            inline=False,
        )

    if announce:
        await announce.send(embed=embed)  # type: ignore[union-attr]

    # Clean up private channels
    if tourn.category:
        await cleanup_category(tourn.category)

    _tournaments.pop(tourn.guild_id, None)
    await db.set_setting(tourn.guild_id, ACTIVE_TOURNAMENT, "")


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class BlackjackCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        tasks.spawn("blackjack:cleanup_orphaned", self._cleanup_orphaned_tournaments())

    async def _cleanup_orphaned_tournaments(self):
        """On startup, find leftover BJ Tournament categories and notify players."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            flag = await db.get_setting(guild.id, ACTIVE_TOURNAMENT, "")
            if flag == "blackjack":
                await db.set_setting(guild.id, ACTIVE_TOURNAMENT, "")
            cat = discord.utils.get(guild.categories, name="BJ Tournament")
            if not cat or not cat.channels:
                continue
            for ch in cat.channels:
                try:
                    await ch.send(
                        "⚠️ The bot restarted and this tournament was interrupted. "
                        "This channel will be deleted in 5 minutes. "
                        "Use `!bjtournament` to start a new one.",
                    )
                except Exception:
                    pass
            await asyncio.sleep(300)
            await cleanup_category(cat)

    # ---- reaction-based tournament registration ----
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.emoji.name != "✅":
            return
        tourn = _tournaments.get(payload.guild_id)
        if not tourn or tourn.started or not tourn.reg_message:
            return
        if payload.message_id != tourn.reg_message.id:
            return
        uid = payload.user_id
        guild = self.bot.get_guild(payload.guild_id)
        if guild and guild.get_member(uid) and guild.get_member(uid).bot:
            return
        ok, _ = await tourn.try_join(uid)
        if ok:
            await _update_tourn_embed(tourn)

    # ---- commands ----

    @commands.command(name="blackjack", aliases=["bj"])
    async def blackjack(
        self,
        ctx: commands.Context,
        target: discord.Member | None = None,
        bet: int = 0,
    ):
        """Play blackjack.  !bj [bet]  or  !bj @player [bet]"""
        if bet < 0:
            await ctx.send("Bet must be 0 or a positive number.", delete_after=5)
            return

        # PvP mode
        if target and target != ctx.author:
            if target.bot:
                await ctx.send("You can't challenge a bot to PvP.", delete_after=5)
                return
            key = frozenset({ctx.author.id, target.id})
            if key in _pvp:
                await ctx.send(
                    "There's already a PvP game between these players.",
                    delete_after=8,
                )
                return
            if bet > 0:
                bal = await db.get_coins(ctx.author.id, ctx.guild.id)
                if bet > bal:
                    await ctx.send(f"❌ You only have **{bal}** 🪙.", delete_after=8)
                    return
            bet_str = f"**{bet}** 🪙" if bet else "free play"
            view = _ChallengeView(ctx.author, target, ctx.guild.id, bet)  # type: ignore[arg-type]
            embed = discord.Embed(
                title="🃏 Blackjack Challenge!",
                description=(
                    f"{ctx.author.mention} challenges {target.mention} to Blackjack "
                    f"({bet_str}).\n{target.mention}, do you accept?"
                ),
                color=SUCCESS_COLOR,
            )
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
            return

        # Solo vs bot
        key = (ctx.author.id, ctx.guild.id)  # type: ignore[assignment]
        if key in _active:
            await ctx.send("You already have a game running!", delete_after=8)
            return
        if bet > 0:
            bal = await db.get_coins(ctx.author.id, ctx.guild.id)
            if bet > bal:
                await ctx.send(f"❌ You only have **{bal}** 🪙.", delete_after=8)
                return

        game = _Game(ctx.author.id, ctx.guild.id, bet)
        _active[key] = game  # type: ignore[index]

        if _is_blackjack(game.player):
            payout = int(bet * 1.5) if bet else FREE_WIN_COINS
            new_bal = await db.add_coins(ctx.author.id, ctx.guild.id, payout)
            embed = _game_embed(game, reveal=True)
            embed.color = ECONOMY_COLOR
            embed.add_field(
                name="🎉 Blackjack!",
                value=f"+{payout} 🪙  |  Balance: **{new_bal}** 🪙",
                inline=False,
            )
            _active.pop(key)  # type: ignore[call-overload]
            await ctx.send(embed=embed)
            return

        view = BlackjackView(game)  # type: ignore[assignment]
        msg = await ctx.send(embed=_game_embed(game), view=view)
        view.message = msg

    @commands.command(name="bjtournament", aliases=["bjtourn"])
    @commands.has_permissions(administrator=True)
    async def bjtournament(
        self,
        ctx: commands.Context,
        entry_fee: int = 0,
        rounds: int = 5,
        duration_mins: int = 5,
    ):
        """Start a Blackjack tournament.  !bjtournament [entry_fee] [rounds] [mins]"""
        if _tournaments.get(ctx.guild.id):
            await ctx.send("A tournament is already running.", delete_after=8)
            return
        existing = await db.get_setting(ctx.guild.id, ACTIVE_TOURNAMENT, "")
        if existing:
            await ctx.send(
                f"A **{existing}** tournament is already active in this server.",
                delete_after=8,
            )
            return
        if entry_fee < 0 or rounds < 1 or duration_mins < 1:
            await ctx.send("Invalid parameters.", delete_after=5)
            return

        tourn = _BjTournament(
            ctx.author.id,
            ctx.guild.id,
            ctx.channel.id,
            entry_fee,
            rounds,
            duration_mins,
        )
        _tournaments[ctx.guild.id] = tourn
        await db.set_setting(ctx.guild.id, ACTIVE_TOURNAMENT, "blackjack")

        view = _TournRegistrationView(tourn)
        msg = await ctx.send(embed=_tourn_embed(tourn), view=view)
        await msg.add_reaction("✅")
        tourn.reg_message = msg

        async def _auto_start():
            await asyncio.sleep(duration_mins * 60)
            if not tourn.started and tourn.guild_id in _tournaments:
                await _launch_tournament(tourn, ctx.guild, ctx.bot)

        tourn.timer_task = tasks.spawn(
            f"blackjack:autostart:{tourn.guild_id}",
            _auto_start(),
        )

    @commands.command(name="bjstart")
    @commands.has_permissions(administrator=True)
    async def bjstart(self, ctx: commands.Context):
        """Manually start a pending Blackjack tournament early."""
        tourn = _tournaments.get(ctx.guild.id)
        if not tourn or tourn.started:
            await ctx.send("No pending tournament.", delete_after=5)
            return
        if tourn.timer_task:
            tourn.timer_task.cancel()
        await _launch_tournament(tourn, ctx.guild, self.bot)

    @commands.command(name="bjstatus")
    async def bjstatus(self, ctx: commands.Context):
        """Show the current tournament status."""
        tourn = _tournaments.get(ctx.guild.id)
        if not tourn:
            await ctx.send("No active tournament.", delete_after=5)
            return
        await ctx.send(embed=_tourn_embed(tourn))


async def _launch_tournament(
    tourn: _BjTournament,
    guild: discord.Guild,
    bot: commands.Bot,
):
    if tourn.started:
        return
    tourn.started = True

    announce = bot.get_channel(tourn.announce_id)
    if not tourn.players:
        if announce:
            await announce.send("❌ Tournament cancelled — no players registered.")  # type: ignore[union-attr]
        _tournaments.pop(tourn.guild_id, None)
        await db.set_setting(tourn.guild_id, ACTIVE_TOURNAMENT, "")
        return

    # Deduct entry fees (uses shared TournamentRegistration helper)
    if tourn.entry_fee:
        await tourn.deduct_fees()

    if not tourn.players:
        if announce:
            await announce.send(  # type: ignore[union-attr]
                "❌ Tournament cancelled — no players could afford the entry fee.",
            )
        _tournaments.pop(tourn.guild_id, None)
        await db.set_setting(tourn.guild_id, ACTIVE_TOURNAMENT, "")
        return

    if announce:
        await announce.send(  # type: ignore[union-attr]
            f"🃏 **Blackjack Tournament starting** with {len(tourn.players)} player(s)! "
            "Check your private channel.",
        )

    # Create private channels via shared utility
    for uid in tourn.players:
        member = guild.get_member(uid)
        if not member:
            tourn.results[uid] = 0
            continue
        try:
            ch = await create_private_channel(
                guild,
                f"bj-{member.display_name}",
                [member],
                "BJ Tournament",
            )
            if tourn.category is None:
                tourn.category = ch.category
            ps = _TournPlayerState(uid, tourn.guild_id, tourn.rounds)
            await ch.send(
                f"Welcome, {member.mention}! You have **{tourn.rounds}** rounds "
                f"and start with **{TOURN_START_CHIPS}** chips. Good luck! 🃏",
            )
            await _start_tourn_round(ps, ch, tourn, bot)
        except discord.Forbidden:
            if announce:
                await announce.send("❌ I don't have permission to create channels.")  # type: ignore[union-attr]
            _tournaments.pop(tourn.guild_id, None)
            await db.set_setting(tourn.guild_id, ACTIVE_TOURNAMENT, "")
            return
        except Exception as e:
            logger.error("Failed to create tournament channel: %s", e)
            tourn.results[uid] = 0

    await _check_tourn_done(tourn, bot)


async def setup(bot: commands.Bot):
    await bot.add_cog(BlackjackCog(bot))
    logger.info("BlackjackCog loaded.")
