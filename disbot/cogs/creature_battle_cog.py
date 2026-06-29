"""Creature PvP battle subsystem — Discord plumbing only (creature-game v1).

The user-facing side of the level-normalized creature PvP flow
(``docs/planning/creature-game-design-and-sim-2026-06-20.md`` §4): ``!cbattle
<opponent>`` opens a challenge the opponent can accept or decline; on accept the
battle auto-resolves and the outcome is posted to the channel.

Domain + boundaries live elsewhere (the "data row / pure math, not code" design):

    utils/creatures/battle.py             — pure combat math (engine)
    services/creature_battle_service.py   — the read boundary (load teams, resolve)
    views/creature_battle/                — the challenge view + outcome renderer

This file hosts only the command and the cog lifecycle. PvP is part of the
**Creatures** subsystem (surfaced through ``creature_cog``'s Help hook, so the
game stays one coherent help entry rather than fragmenting into a second
subsystem); it is hub-less for this slice (like catch/fishing). A separate flat
cog file (not a ``cogs/creature_battle/`` package) mirrors the sibling
``creature_cog.py`` — one command doesn't warrant a package.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import guild_resources as resources
from utils import db
from views.creature import (
    CreatureMenuView,
    build_battletop_embed,
    build_menu_embed,
    build_record_embed,
)
from views.creature.menu import load_progress
from views.creature_battle import CreatureBattleChallengeView

logger = logging.getLogger("bot.cogs.creature_battle")


class CreatureBattleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu hook — the shared Creatures panel.

        ``cbattle`` / ``cbrecord`` / ``cbattletop`` are part of the **creature**
        subsystem (this is its PvP cog), so the help dropdown can route here; it
        lands on the same :class:`CreatureMenuView` the catch cog returns, so the
        whole game is one coherent panel (the Challenge button opens the PvP flow).
        """
        caught_unique, level, _ = await load_progress(
            interaction.user.id,
            interaction.guild.id,
        )
        return build_menu_embed(caught_unique, level), CreatureMenuView(
            interaction.user,
            interaction.guild.id,
        )

    @commands.command(name="cbattle", aliases=["creaturebattle"])
    async def cbattle(self, ctx, opponent: discord.Member):
        """Challenge another member to a level-normalized creature PvP battle."""
        if opponent.bot:
            await ctx.send("🤖 You can't battle a bot — challenge a real trainer!")
            return
        if opponent.id == ctx.author.id:
            await ctx.send("🪞 You can't battle yourself — challenge someone else!")
            return
        view = CreatureBattleChallengeView(ctx.author, opponent, ctx.guild.id)
        view.message = await ctx.send(
            f"{opponent.mention} — {ctx.author.mention} challenges you to a "
            "creature battle! Teams are level-normalized; your collection and "
            "type matchups decide it.",
            view=view,
        )

    @commands.command(name="cbrecord", aliases=["battlerecord"])
    async def cbrecord(self, ctx, member: discord.Member | None = None):
        """Show your (or another trainer's) creature PvP win/loss record."""
        target = member or ctx.author
        wins, losses = await db.get_battle_record(target.id, ctx.guild.id)
        await ctx.send(embed=build_record_embed(target.display_name, wins, losses))

    @commands.command(name="cbattletop", aliases=["pvptop", "battletop"])
    async def cbattletop(self, ctx):
        """Show this server's top creature-PvP trainers by wins."""
        rows = await db.top_battlers(ctx.guild.id)

        def _name(user_id: int) -> str:
            member = resources.resolve_member(ctx.guild, user_id)
            return member.display_name if member else f"User {user_id}"

        await ctx.send(embed=build_battletop_embed(rows, _name))


async def setup(bot):
    await bot.add_cog(CreatureBattleCog(bot))
