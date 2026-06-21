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

from views.creature_battle import CreatureBattleChallengeView

logger = logging.getLogger("bot.cogs.creature_battle")


class CreatureBattleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

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


async def setup(bot):
    await bot.add_cog(CreatureBattleCog(bot))
