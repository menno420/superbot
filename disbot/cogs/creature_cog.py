"""Creature subsystem — Discord plumbing only (creature-game v1, catch slice).

The runtime side of ``docs/planning/creature-game-design-and-sim-2026-06-20.md``
(Q-0186/Q-0187): catch **original** creatures (no Pokémon IP) and fill out a
collection "dex". Wild encounters are rarity-weighted (Common common, Epic rare);
rarer creatures are harder to catch. Leveling reuses the shared ``game_xp`` track.
The level-normalized **PvP battle** is a later substantial-runtime slice.

Domain logic, the audited write boundary, and the data live in their own modules:

    utils/creatures/                 — pure domain (catalog, encounter, catch roll)
    services/creature_workflow.py    — the audited write boundary
    utils/db/games/creatures.py      — the collection-log CRUD
    disbot/data/creatures/...        — the 36-creature catalog

This file hosts the commands, the cog lifecycle, and the Help-menu hook. The
interactive Games-hub panel (catch / dex-browser / challenge / ladder) lives in
:mod:`views.creature.menu` — reached via ``!creatures`` and the Help hook (the
completion-cert deepening, Q-0209); the typed ``!catch`` / ``!dex`` commands stay
for the keyboard-first path. Every embed is built by :mod:`views.creature.embeds`
so the panel and the commands can't drift.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import guild_resources as resources
from services import creature_workflow
from utils import db
from utils.creatures import creature_names
from views.creature import (
    CreatureMenuView,
    build_catch_result_embed,
    build_collectors_embed,
    build_dex_embed,
    build_menu_embed,
)
from views.creature.menu import load_progress

logger = logging.getLogger("bot.cogs.creature")


class CreatureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    # ------------------------------------------------------------------ commands

    @commands.command(aliases=["hunt"])
    async def catch(self, ctx):
        """Head into the wild to find and catch a creature."""
        result = await creature_workflow.catch(ctx.author.id, ctx.guild.id)
        # The mention pings the catcher (keyboard path); the embed body is built by
        # the shared builder so it can't drift from the panel's Catch button.
        await ctx.send(
            content=ctx.author.mention,
            embed=build_catch_result_embed(ctx.author.display_name, result),
        )

    @commands.command(name="creatures", aliases=["creaturemenu", "pets"])
    async def creatures(self, ctx):
        """Open the interactive Creatures panel — catch, browse your dex, battle."""
        caught_unique, level, _ = await load_progress(ctx.author.id, ctx.guild.id)
        await ctx.send(
            embed=build_menu_embed(caught_unique, level),
            view=CreatureMenuView(ctx.author, ctx.guild.id),
        )

    @commands.command(name="dex", aliases=["collection"])
    async def dex(self, ctx):
        """Show your creature collection — every creature you've caught."""
        _, level, log = await load_progress(ctx.author.id, ctx.guild.id)
        embed = build_dex_embed(ctx.author.display_name, log, level)
        await ctx.send(embed=embed)

    @commands.command(name="dextop", aliases=["topcatchers"])
    async def dextop(self, ctx):
        """Show this server's top collectors by total creatures caught."""
        rows = await db.top_collectors(ctx.guild.id, creature_names())

        def _name(user_id: int) -> str:
            member = resources.resolve_member(ctx.guild, user_id)
            return member.display_name if member else f"User {user_id}"

        await ctx.send(embed=build_collectors_embed(rows, _name))

    # ------------------------------------------------------------------ help hook

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — the interactive Creatures panel.

        Returns the live :class:`CreatureMenuView` (🐾 Catch · 📖 Dex · ⚔️ Challenge
        · 🏆 Ladder) so the Games-hub → Creatures path lands on a playable surface,
        not a static overview (completion cert #1, Q-0209).
        """
        caught_unique, level, _ = await load_progress(
            interaction.user.id,
            interaction.guild.id,
        )
        return build_menu_embed(caught_unique, level), CreatureMenuView(
            interaction.user,
            interaction.guild.id,
        )


async def setup(bot):
    await bot.add_cog(CreatureCog(bot))
