from __future__ import annotations
import random
import discord
from discord.ext import commands
import logging
from utils import db

logger = logging.getLogger("bot")

# ---------------------------------------------------------------------------
# Card engine
# ---------------------------------------------------------------------------

SUITS = ("♠", "♥", "♦", "♣")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
FREE_WIN_COINS = 50


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
    def __init__(self, user_id: int, guild_id: int, bet: int):
        self.user_id = user_id
        self.guild_id = guild_id
        self.bet = bet           # 0 = free play
        self.doubled = False
        self.deck = _new_deck()
        self.player: list[str] = [self.deck.pop(), self.deck.pop()]
        self.dealer: list[str] = [self.deck.pop(), self.deck.pop()]

    def hit(self) -> str:
        card = self.deck.pop()
        self.player.append(card)
        return card

    def dealer_play(self):
        while _hand_value(self.dealer) < 17:
            self.dealer.append(self.deck.pop())


# Active games: (user_id, guild_id) → _Game
_active: dict[tuple[int, int], _Game] = {}


# ---------------------------------------------------------------------------
# Embed builder
# ---------------------------------------------------------------------------

def _build_embed(game: _Game, reveal: bool = False) -> discord.Embed:
    pv = _hand_value(game.player)
    dv = _hand_value(game.dealer) if reveal else _rank_value(game.dealer[0].split()[0])

    if reveal:
        dealer_str = _hand_str(game.dealer)
        dealer_label = f"Dealer ({dv})"
    else:
        dealer_str = _hand_str(game.dealer, hide_second=True)
        dealer_label = f"Dealer ({_rank_value(game.dealer[0].split()[0])}+?)"

    bet_str = f"**{game.bet}** 🪙" if game.bet else "Free play (win = +50 🪙)"
    embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.dark_green())
    embed.add_field(name=dealer_label, value=dealer_str, inline=False)
    embed.add_field(name=f"Your hand ({pv})", value=_hand_str(game.player), inline=False)
    embed.add_field(name="Bet", value=bet_str, inline=True)
    return embed


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class BlackjackView(discord.ui.View):
    def __init__(self, game: _Game):
        super().__init__(timeout=120)
        self.game = game
        self.message: discord.Message | None = None
        # Disable double-down if player can't afford 2× or game not at start
        self.double_btn.disabled = game.bet == 0  # can't double a free game

    async def _end(
        self,
        interaction: discord.Interaction,
        *,
        result: str,
        color: discord.Color,
        coin_delta: int,
    ):
        key = (self.game.user_id, self.game.guild_id)
        _active.pop(key, None)
        for item in self.children:
            item.disabled = True

        embed = _build_embed(self.game, reveal=True)
        embed.color = color
        new_bal = await db.add_coins(self.game.user_id, self.game.guild_id, coin_delta)
        delta_str = f"+{coin_delta}" if coin_delta >= 0 else str(coin_delta)
        embed.add_field(
            name=result,
            value=f"{delta_str} 🪙  |  Balance: **{new_bal}** 🪙",
            inline=False,
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message(
                "This game isn't yours.", ephemeral=True
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

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green, emoji="👊")
    async def hit_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.game.hit()
        pv = _hand_value(self.game.player)

        if pv > 21:
            bet = self.game.bet if not self.game.doubled else self.game.bet * 2
            await self._end(
                interaction,
                result="💥 Bust — you lose!",
                color=discord.Color.red(),
                coin_delta=-bet if bet else 0,
            )
            return

        # After a hit you can no longer double
        self.double_btn.disabled = True
        embed = _build_embed(self.game)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.grey, emoji="✋")
    async def stand_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._resolve(interaction)

    @discord.ui.button(label="Double Down", style=discord.ButtonStyle.blurple, emoji="✌️")
    async def double_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Check player has enough coins
        bal = await db.get_coins(self.game.user_id, self.game.guild_id)
        if bal < self.game.bet * 2:
            await interaction.response.send_message(
                f"❌ Not enough coins to double down (need {self.game.bet * 2}, have {bal}).",
                ephemeral=True,
            )
            return
        self.game.hit()
        self.game.doubled = True
        pv = _hand_value(self.game.player)
        if pv > 21:
            await self._end(
                interaction,
                result="💥 Bust — you lose!",
                color=discord.Color.red(),
                coin_delta=-(self.game.bet * 2),
            )
            return
        await self._resolve(interaction)

    async def _resolve(self, interaction: discord.Interaction):
        self.game.dealer_play()
        pv = _hand_value(self.game.player)
        dv = _hand_value(self.game.dealer)
        effective_bet = self.game.bet * 2 if self.game.doubled else self.game.bet

        if _is_blackjack(self.game.player) and len(self.game.dealer) == 2:
            # Natural blackjack beats everything (pays 3:2, floor)
            payout = int(effective_bet * 1.5) if effective_bet else FREE_WIN_COINS
            await self._end(
                interaction,
                result="🎉 Blackjack! You win!",
                color=discord.Color.gold(),
                coin_delta=payout,
            )
        elif dv > 21:
            payout = effective_bet if effective_bet else FREE_WIN_COINS
            await self._end(
                interaction,
                result="🎉 Dealer busts — you win!",
                color=discord.Color.green(),
                coin_delta=payout,
            )
        elif pv > dv:
            payout = effective_bet if effective_bet else FREE_WIN_COINS
            await self._end(
                interaction,
                result="🎉 You win!",
                color=discord.Color.green(),
                coin_delta=payout,
            )
        elif pv == dv:
            await self._end(
                interaction,
                result="🤝 Push — it's a tie.",
                color=discord.Color.blurple(),
                coin_delta=0,
            )
        else:
            loss = -(effective_bet) if effective_bet else 0
            await self._end(
                interaction,
                result="😞 Dealer wins.",
                color=discord.Color.red(),
                coin_delta=loss,
            )


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class BlackjackCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="blackjack", aliases=["bj"])
    async def blackjack(self, ctx: commands.Context, bet: int = 0):
        """Play blackjack.  !blackjack [bet]  (0 = free, win = +50 🪙)"""
        key = (ctx.author.id, ctx.guild.id)
        if key in _active:
            await ctx.send(
                "You already have a blackjack game running! Finish it first.",
                delete_after=10,
            )
            return

        if bet < 0:
            await ctx.send("Bet must be 0 (free) or a positive number.", delete_after=5)
            return

        if bet > 0:
            bal = await db.get_coins(ctx.author.id, ctx.guild.id)
            if bet > bal:
                await ctx.send(
                    f"❌ You only have **{bal}** 🪙. You can't bet **{bet}**.",
                    delete_after=10,
                )
                return

        game = _Game(ctx.author.id, ctx.guild.id, bet)
        _active[key] = game

        # Instant blackjack on deal
        if _is_blackjack(game.player):
            payout = int(bet * 1.5) if bet else FREE_WIN_COINS
            new_bal = await db.add_coins(ctx.author.id, ctx.guild.id, payout)
            embed = _build_embed(game, reveal=True)
            embed.color = discord.Color.gold()
            embed.add_field(
                name="🎉 Blackjack!",
                value=f"+{payout} 🪙  |  Balance: **{new_bal}** 🪙",
                inline=False,
            )
            _active.pop(key)
            await ctx.send(embed=embed)
            return

        view = BlackjackView(game)
        embed = _build_embed(game)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg


async def setup(bot: commands.Bot):
    await bot.add_cog(BlackjackCog(bot))
    logger.info("BlackjackCog loaded.")
