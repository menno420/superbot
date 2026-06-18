"""Fishing subsystem — Discord plumbing only (S4.1 decomposition).

Ecosystem #2 (the second character-platform activity), PR 1 — the core loop.
Domain logic, the audited write boundary, and the reward policy live in their
own modules per ``docs/architecture.md`` §"Subsystem decomposition":

    utils/fishing/                 — pure domain (species catalog, catch roll)
    services/fishing_workflow.py   — the audited write boundary
    utils/db/games/fishing.py      — the collection-log CRUD

This file hosts only commands, the cog lifecycle, and the Help-menu hook.
Fishing is **hub-less** for now (surfaced via its Help hook, like
``welcome``/``counters``); the open-world Explore hub that folds ``!fish`` into
a 🎣 button is a later plan slice
(``docs/planning/fishing-ecosystem-plan-2026-06-18.md``).
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import guild_resources as resources
from services import fishing_workflow, game_xp_service
from utils import db
from utils.fishing.fish import SPECIES
from utils.ui_constants import INFO_COLOR

logger = logging.getLogger("bot.cogs.fishing")

_FISHING_COLOR = discord.Color.blue()


class FishingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    # ------------------------------------------------------------------ commands

    @commands.command()
    async def fish(self, ctx):
        """Cast a line and catch a fish — earns coins and game XP."""
        result = await fishing_workflow.fish(ctx.author.id, ctx.guild.id)
        catch = result.catch
        message = (
            f"{ctx.author.mention} 🎣 cast a line and reeled in "
            f"{catch.species.emoji} a **{catch.species.name.title()}** "
            f"({catch.weight} kg, *{catch.species.rarity}*) "
            f"for **{result.coins}** 🪙! "
            f"Balance: **{result.new_balance}** 🪙."
        )
        if result.xp_note:
            message += "\n" + result.xp_note
        await ctx.send(message)

    @commands.command(
        name="fishlog",
        aliases=["fishdex"],
    )
    async def fishlog(self, ctx):
        """Show your fishing collection — every species you've caught."""
        log = await db.get_fishing_log(ctx.author.id, ctx.guild.id)
        level, into, needed = await game_xp_service.level_info(
            ctx.guild.id,
            ctx.author.id,
        )
        embed = discord.Embed(
            title=f"🎣 {ctx.author.display_name}'s Fishing Log",
            color=_FISHING_COLOR,
        )
        caught = len(log)
        total_catches = sum(e["count"] for e in log.values())
        total_value = sum(e["total_value"] for e in log.values())
        embed.description = (
            f"**{caught}/{len(SPECIES)}** species discovered · "
            f"**{total_catches}** catches · **{total_value}** 🪙 earned · "
            f"Game Level **{level}**"
        )
        if log:
            lines = []
            for species in SPECIES:
                entry = log.get(species.name)
                if entry is None:
                    continue
                lines.append(
                    f"{species.emoji} **{species.name.title()}** ×{entry['count']} "
                    f"· best {entry['best_weight']} kg · {entry['total_value']} 🪙",
                )
            embed.add_field(
                name="Caught",
                value="\n".join(lines),
                inline=False,
            )
        else:
            embed.add_field(
                name="No catches yet",
                value="Cast your first line with `!fish`!",
                inline=False,
            )
        embed.set_footer(text="!fish to cast · !fishtop for the server leaderboard")
        await ctx.send(embed=embed)

    @commands.command(
        name="fishtop",
        aliases=["topfishers"],
    )
    async def fishtop(self, ctx):
        """Show this server's top anglers by coins earned from fishing."""
        rows = await db.top_fishers(ctx.guild.id)
        embed = discord.Embed(title="🎣 Top Anglers", color=_FISHING_COLOR)
        if not rows:
            embed.description = (
                "No one has cast a line yet — be the first with `!fish`!"
            )
            await ctx.send(embed=embed)
            return
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for rank, (user_id, caught, value) in enumerate(rows):
            prefix = medals[rank] if rank < len(medals) else f"**{rank + 1}.**"
            member = resources.resolve_member(ctx.guild, user_id)
            name = member.display_name if member else f"User {user_id}"
            lines.append(f"{prefix} {name} — **{value}** 🪙 ({caught} catches)")
        embed.description = "\n".join(lines)
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------ help hook

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — a static fishing overview.

        Fishing is hub-less (no persistent panel yet), so this returns a plain
        informational embed + an empty view (the Help framework's contract).
        """
        embed = discord.Embed(
            title="🎣 Fishing",
            description=(
                "Cast a line to catch fish for coins and game XP, and fill out "
                "your collection log.\n\n"
                "**`!fish`** — cast a line\n"
                "**`!fishlog`** — your collection\n"
                "**`!fishtop`** — the server leaderboard"
            ),
            color=INFO_COLOR,
        )
        return embed, discord.ui.View()


async def setup(bot):
    await bot.add_cog(FishingCog(bot))
