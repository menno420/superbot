"""Single-player Rock·Paper·Scissors view.

Three buttons → pick a move → resolve against a random bot pick →
apply the coin delta via :mod:`services.economy_service`.

The bet is not pre-escrowed (the user can play with zero balance and
lose nothing more than they already have).  Win credits, loss debits
with overdraft allowed to preserve the original floor-at-zero
behaviour.

After resolution ``_RpsView`` hands the message off to a fresh
``_RpsSoloResultView`` — same three disabled Rock/Paper/Scissors
shells on row 0, plus ``🔁 Play again`` / ``↩ Back to RPS`` on row
1. Swapping the view (rather than appending buttons and calling
``stop()`` on the original) keeps the terminal-state buttons
dispatchable: the original view's ``stop()`` un-registers it from
discord.py's component dispatch table, and any buttons still bound
to it would surface "interaction failed" on click. ``Play again``
spawns a fresh ``_RpsView`` with the same user/guild/bet (after a
balance pre-check when ``bet > 0``); ``Back to RPS`` returns to
``RPSPanelView`` via the shared ``BackToPanelButton``.
"""

from __future__ import annotations

import random

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services import economy_service
from utils import db as global_db
from utils.ui_constants import ERROR_COLOR, GAME_COLOR, SUCCESS_COLOR
from views.rps._helpers import _FREE_WIN, _RPS_EMOJI, _RPS_WINS


class _RpsView(discord.ui.View):
    def __init__(self, user: discord.Member, guild_id: int, bet: int):
        super().__init__(timeout=60)
        self.user = user
        self.guild_id = guild_id
        self.bet = bet
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This game isn't yours.",
                ephemeral=True,
            )
            return False
        return True

    async def _play(self, interaction: discord.Interaction, player_move: str):
        # Defer up front — the economy write below races the 3 s
        # interaction token under load.
        if not await safe_defer(interaction):
            return

        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]

        bot_move = random.choice(["rock", "paper", "scissors"])
        pe, be = _RPS_EMOJI[player_move], _RPS_EMOJI[bot_move]

        if player_move == bot_move:
            result = "🤝 Tie!"
            coin_delta = 0
            color = GAME_COLOR
        elif _RPS_WINS[player_move] == bot_move:
            payout = self.bet if self.bet else _FREE_WIN
            result = f"🎉 You win! +{payout} 🪙"
            coin_delta = payout
            color = SUCCESS_COLOR
        else:
            loss = -self.bet if self.bet else 0
            result = f"😞 Bot wins. {loss} 🪙" if self.bet else "😞 Bot wins."
            coin_delta = loss
            color = ERROR_COLOR

        # Single-player RPS: bet was not pre-deducted, outcome is applied
        # directly. Positive coin_delta = win (credit), negative = loss (debit
        # with overdraft to preserve the original floor-at-zero behaviour).
        if coin_delta > 0:
            new_bal = await economy_service.credit(
                self.guild_id,
                self.user.id,
                coin_delta,
                reason="rps:solo_win",
                actor_id=self.user.id,
            )
        elif coin_delta < 0:
            new_bal = await economy_service.debit(
                self.guild_id,
                self.user.id,
                -coin_delta,
                reason="rps:solo_loss",
                actor_id=self.user.id,
                allow_overdraft=True,
            )
        else:
            new_bal = await global_db.get_coins(self.user.id, self.guild_id)
        embed = discord.Embed(
            title="✂️ Rock · Paper · Scissors",
            description=(
                f"You: **{player_move}** {pe}  vs  Bot: **{bot_move}** {be}\n\n"
                f"{result}\n"
                f"Balance: **{new_bal}** 🪙"
            ),
            color=color,
        )

        result_view = _RpsSoloResultView(self.user, self.guild_id, self.bet)
        await safe_edit(interaction, embed=embed, view=result_view)
        result_view.message = interaction.message
        self.stop()

    @discord.ui.button(label="Rock", emoji="🪨", style=discord.ButtonStyle.grey)
    async def rock(self, i: discord.Interaction, _: discord.ui.Button):
        await self._play(i, "rock")

    @discord.ui.button(label="Paper", emoji="📄", style=discord.ButtonStyle.grey)
    async def paper(self, i: discord.Interaction, _: discord.ui.Button):
        await self._play(i, "paper")

    @discord.ui.button(label="Scissors", emoji="✂️", style=discord.ButtonStyle.grey)
    async def scissors(self, i: discord.Interaction, _: discord.ui.Button):
        await self._play(i, "scissors")

    async def on_timeout(self):
        if self.message is None:
            return
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            await self.message.edit(content="Game timed out.", view=self)
        except Exception:
            pass


class _RpsSoloResultView(discord.ui.View):
    """Terminal-state view shown after a solo RPS round resolves.

    Replaces the live ``_RpsView`` once ``_play`` settles so that Play
    again / Back stay independently dispatchable. The previous design
    appended these buttons to the still-attached ``_RpsView`` and
    called ``self.stop()`` on it — which removes the view from
    discord.py's component dispatch table and leaves the visible
    buttons unable to respond (Discord renders "interaction failed").
    """

    def __init__(self, user: discord.Member, guild_id: int, bet: int) -> None:
        super().__init__(timeout=60)
        self.user = user
        self.guild_id = guild_id
        self.bet = bet
        self.message: discord.Message | None = None

        for label, emoji in (
            ("Rock", "🪨"),
            ("Paper", "📄"),
            ("Scissors", "✂️"),
        ):
            self.add_item(
                discord.ui.Button(
                    label=label,
                    emoji=emoji,
                    style=discord.ButtonStyle.grey,
                    disabled=True,
                    row=0,
                ),
            )

        replay_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="🔁 Play again",
            style=discord.ButtonStyle.success,
            custom_id="rps:solo:replay",
            row=1,
        )
        replay_btn.callback = self._replay  # type: ignore[method-assign]
        self.add_item(replay_btn)

        # Late import: rps_panel imports _RpsView, so a module-level
        # import would create a cycle.
        from views.games.rps_panel import _make_rps_back_button

        back_btn = _make_rps_back_button()
        back_btn.row = 1
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This game isn't yours.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if self.message is None:
            return
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            await self.message.edit(view=self)
        except Exception:
            pass

    async def _replay(self, interaction: discord.Interaction) -> None:
        """Spawn a fresh ``_RpsView`` with the same user/guild/bet.

        Mirrors the canonical RPS solo start shape used by
        ``cogs.rps_tournament._quickplay`` and
        ``views.games.rps_panel`` — balance check when ``bet > 0``
        then construct ``_RpsView(user, guild_id, bet)``. No public
        ``start_solo_rps`` exists; this construction *is* the
        canonical entry surface (helper-policy: single caller).
        """
        if not await safe_defer(interaction):
            return

        if self.bet > 0:
            bal = await global_db.get_coins(self.user.id, self.guild_id)
            if bal < self.bet:
                await safe_followup(
                    interaction,
                    (
                        f"❌ Need **{self.bet}** 🪙 to replay at the same bet "
                        f"(you have **{bal}**). Use **↩ Back to RPS** to pick "
                        "a new bet or play free."
                    ),
                    ephemeral=True,
                )
                return

        from views.games.rps_panel import build_rps_solo_embed

        new_view = _RpsView(self.user, self.guild_id, self.bet)
        await safe_edit(
            interaction,
            embed=build_rps_solo_embed(self.bet),
            view=new_view,
        )
        new_view.message = interaction.message
