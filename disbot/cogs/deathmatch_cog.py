from __future__ import annotations

import random

import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from utils import db


class _Duel:
    def __init__(self, player1: discord.Member, player2: discord.Member):
        self.player1 = player1
        self.player2 = player2
        self.player1_hp = 100
        self.player2_hp = 100
        self.turn = player1
        self.is_over = False
        self.defense: dict[int, bool] = {player1.id: False, player2.id: False}

    def attack(self, attacker_id: int, defender_id: int) -> tuple[int, bool]:
        critical = random.random() < 0.1
        damage = 30 if critical else 15
        if self.defense.get(defender_id, False):
            damage = damage // 2
            self.defense[defender_id] = False
        if defender_id == self.player1.id:
            self.player1_hp -= damage
        else:
            self.player2_hp -= damage
        return damage, critical

    def defend(self, player_id: int) -> None:
        self.defense[player_id] = True


class _DuelView(discord.ui.View):
    def __init__(
        self,
        cog: Deathmatch,
        duel: _Duel,
        duel_key: tuple,
        ctx: commands.Context,
    ):
        super().__init__(timeout=60.0)
        self.cog = cog
        self.duel = duel
        self.duel_key = duel_key
        self.ctx = ctx
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.duel.turn:
            await interaction.response.send_message(
                "It's not your turn!",
                ephemeral=True,
            )
            return False
        return True

    def build_embed(self, last_action: str = "") -> discord.Embed:
        duel = self.duel
        desc = (
            f"**{duel.player1.display_name}** — {max(duel.player1_hp, 0)} HP\n"
            f"**{duel.player2.display_name}** — {max(duel.player2_hp, 0)} HP\n\n"
            f"It's **{duel.turn.display_name}**'s turn!"
        )
        if last_action:
            desc += f"\n\n{last_action}"
        return discord.Embed(
            title="⚔️ Deathmatch In Progress",
            description=desc,
            color=discord.Color.dark_red(),
        )

    async def on_timeout(self) -> None:
        duel = self.duel
        if duel.is_over:
            return
        opponent = duel.player2 if duel.turn == duel.player1 else duel.player1
        duel.is_over = True
        self.cog.active_duels.pop(self.duel_key, None)
        await self.cog.update_leaderboard(winner_id=opponent.id, loser_id=duel.turn.id)
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        embed = discord.Embed(
            title="⚔️ Deathmatch — Timeout",
            description=(
                f"{duel.turn.mention} took too long to respond.\n"
                f"🏆 {opponent.mention} wins by default!"
            ),
            color=discord.Color.orange(),
        )
        if self.message:
            try:
                await self.message.edit(embed=embed, view=self)
            except Exception:
                pass

    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger, row=0)
    async def btn_attack(self, interaction: discord.Interaction, _: discord.ui.Button):
        duel = self.duel
        current = duel.turn
        opponent = duel.player2 if current == duel.player1 else duel.player1
        damage, critical = duel.attack(current.id, opponent.id)
        result = f"**{current.display_name}** attacks for **{damage} damage**!"
        if critical:
            result += " ⚡ **Critical Hit!**"
        await self._resolve(interaction, result)

    @discord.ui.button(label="🛡️ Defend", style=discord.ButtonStyle.blurple, row=0)
    async def btn_defend(self, interaction: discord.Interaction, _: discord.ui.Button):
        duel = self.duel
        current = duel.turn
        duel.defend(current.id)
        await self._resolve(
            interaction,
            f"🛡️ **{current.display_name}** takes a defensive stance!",
        )

    async def _resolve(
        self,
        interaction: discord.Interaction,
        action_text: str,
    ) -> None:
        duel = self.duel
        current = duel.turn
        opponent = duel.player2 if current == duel.player1 else duel.player1
        duel.turn = opponent

        winner = loser = None
        if duel.player1_hp <= 0:
            winner, loser = duel.player2, duel.player1
        elif duel.player2_hp <= 0:
            winner, loser = duel.player1, duel.player2

        if winner:
            duel.is_over = True
            self.cog.active_duels.pop(self.duel_key, None)
            await self.cog.update_leaderboard(winner_id=winner.id, loser_id=loser.id)
            for item in self.children:
                item.disabled = True  # type: ignore[attr-defined]
            embed = discord.Embed(
                title="⚔️ Deathmatch Ended",
                description=(
                    f"{action_text}\n\n"
                    f"**{duel.player1.display_name}** — {max(duel.player1_hp, 0)} HP\n"
                    f"**{duel.player2.display_name}** — {max(duel.player2_hp, 0)} HP\n\n"
                    f"🏆 {winner.mention} wins!"
                ),
                color=discord.Color.gold(),
            )
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.edit_message(
                embed=self.build_embed(action_text),
                view=self,
            )


class _ChallengeView(discord.ui.View):
    def __init__(
        self,
        cog: Deathmatch,
        challenger: discord.Member,
        opponent: discord.Member,
        duel_key: tuple,
        ctx: commands.Context,
    ):
        super().__init__(timeout=30.0)
        self.cog = cog
        self.challenger = challenger
        self.opponent = opponent
        self.duel_key = duel_key
        self.ctx = ctx
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.opponent:
            await interaction.response.send_message(
                "This challenge is not for you!",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        embed = discord.Embed(
            title="⚔️ Challenge Expired",
            description=f"{self.opponent.mention} did not respond in time.",
            color=discord.Color.greyple(),
        )
        if self.message:
            try:
                await self.message.edit(embed=embed, view=self)
            except Exception:
                pass

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.green)
    async def btn_accept(self, interaction: discord.Interaction, _: discord.ui.Button):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        duel = _Duel(self.challenger, self.opponent)
        self.cog.active_duels[self.duel_key] = duel
        duel_view = _DuelView(self.cog, duel, self.duel_key, self.ctx)
        await interaction.response.edit_message(
            embed=duel_view.build_embed(),
            view=duel_view,
        )
        duel_view.message = await interaction.original_response()

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger)
    async def btn_decline(self, interaction: discord.Interaction, _: discord.ui.Button):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        embed = discord.Embed(
            title="⚔️ Challenge Declined",
            description=f"{self.opponent.mention} declined the duel.",
            color=discord.Color.greyple(),
        )
        await interaction.response.edit_message(embed=embed, view=self)


class Deathmatch(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.active_duels: dict[tuple, _Duel] = {}

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — returns the Deathmatch panel.

        PR 6 replaced the previous empty ``discord.ui.View()`` with
        :class:`DeathmatchPanelView` so the panel is actionable from
        Help/Games (Fight Bot / Challenge Player / Rules buttons).
        """
        from views.games.deathmatch_panel import (
            DeathmatchPanelView,
            build_deathmatch_overview_embed,
        )

        view = DeathmatchPanelView(interaction.user)
        return build_deathmatch_overview_embed(), view

    @commands.command(name="dm_challenge", aliases=["deathmatch", "challenge", "dm"])
    @cooldown(1, 30, BucketType.user)
    async def challenge(self, ctx: commands.Context, opponent: discord.Member):
        """Challenge another user to a deathmatch duel."""
        if opponent == ctx.author:
            await ctx.send("You cannot challenge yourself!")
            return
        if opponent.bot:
            await ctx.send("You cannot challenge a bot!")
            return

        duel_key = tuple(sorted([ctx.author.id, opponent.id]))
        if duel_key in self.active_duels:
            await ctx.send(
                "A duel between you and the opponent is already in progress.",
            )
            return
        for existing_key in self.active_duels:
            if ctx.author.id in existing_key or opponent.id in existing_key:
                await ctx.send("Either you or the opponent is already in a duel.")
                return

        embed = discord.Embed(
            title="⚔️ Deathmatch Challenge",
            description=(
                f"{ctx.author.mention} has challenged {opponent.mention} to a duel!\n\n"
                "Press **Accept** or **Decline** below."
            ),
            color=discord.Color.red(),
        )
        embed.set_footer(text="You have 30 seconds to respond.")
        view = _ChallengeView(self, ctx.author, opponent, duel_key, ctx)  # type: ignore[arg-type]
        view.message = await ctx.send(embed=embed, view=view)

    async def update_leaderboard(self, winner_id: int, loser_id: int) -> None:
        await db.update_deathmatch(winner_id, loser_id)

    @challenge.error
    async def challenge_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"You're on cooldown! Please try again in {int(error.retry_after)} seconds.",
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Couldn't find the user. Please mention a valid member.")
        else:
            await ctx.send("An error occurred while processing the command.")
            raise error

    @commands.command(name="dm_help", aliases=["deathmatch_help"])
    async def dm_help(self, ctx: commands.Context):
        """Display help information for Deathmatch commands."""
        embed = discord.Embed(
            title="Deathmatch Help",
            description=(
                "**Commands:**\n"
                "`!deathmatch @User` — Challenge a user to a duel.\n"
                "`!leaderboard deathmatch` — View the top duelists.\n\n"
                "**During a Duel:**\n"
                "Use the **⚔️ Attack** and **🛡️ Defend** buttons in the duel message."
            ),
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Deathmatch(bot))
