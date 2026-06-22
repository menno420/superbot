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

This file hosts only commands, the cog lifecycle, and the Help-menu hook.
Creatures are **hub-less** for this slice (surfaced via its Help hook + the typed
commands, exactly like ``fishing``); folding 🐾 Creatures into the open-world
Explore hub is a later plan slice.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import guild_resources as resources
from services import creature_workflow, game_xp_service
from utils import db
from utils.creatures import CREATURES, creature_names
from utils.ui_constants import INFO_COLOR

logger = logging.getLogger("bot.cogs.creature")

_CREATURE_COLOR = discord.Color.green()


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
        if result.creature is None:
            await ctx.send("🐾 The wilds are quiet right now — try again later.")
            return
        creature = result.creature
        if not result.caught:
            await ctx.send(
                f"{ctx.author.mention} 🐾 spotted a wild "
                f"{creature.emoji} **{creature.name}** ({creature.rarity} "
                f"{creature.element}) — but it got away! Try again.",
            )
            return
        message = (
            f"{ctx.author.mention} 🎉 caught {creature.emoji} a "
            f"**{creature.name}**! ({creature.rarity} {creature.element})"
        )
        if result.is_new:
            message += "\n✨ **New dex entry!**"
        if result.xp_note:
            message += "\n" + result.xp_note
        await ctx.send(message)

    @commands.command(name="dex", aliases=["collection", "creatures"])
    async def dex(self, ctx):
        """Show your creature collection — every creature you've caught."""
        log = await db.get_creature_collection(ctx.author.id, ctx.guild.id)
        xp_map = await db.get_game_xp(ctx.author.id, ctx.guild.id)
        creature_xp = xp_map.get(game_xp_service.GAME_CREATURE, 0)
        level = creature_workflow.creature_level_from_xp(creature_xp)

        # Count only current-catalog creatures so legacy rows from a superseded
        # roster never show impossible progress (the fishing reconciliation lesson).
        known = {c.name for c in CREATURES}
        caught_unique = sum(1 for name in log if name in known)
        total = sum(c for name, c in log.items() if name in known)
        embed = discord.Embed(
            title=f"🐾 {ctx.author.display_name}'s Creature Dex",
            color=_CREATURE_COLOR,
        )
        embed.description = (
            f"**{caught_unique}/{len(CREATURES)}** creatures discovered · "
            f"**{total}** total catches · Creature level **{level}**"
        )
        # Group the dex by element for a readable roster.
        by_element: dict[str, list[str]] = {}
        for creature in CREATURES:
            count = log.get(creature.name, 0)
            if count:
                line = f"{creature.emoji} **{creature.name}** ×{count}"
            else:
                line = f"{creature.emoji} {creature.name} — *not yet caught*"
            by_element.setdefault(creature.element, []).append(line)
        for element, lines in by_element.items():
            embed.add_field(name=element, value="\n".join(lines), inline=True)
        embed.set_footer(text="!catch to hunt · !dextop for the leaderboard")
        await ctx.send(embed=embed)

    @commands.command(name="dextop", aliases=["topcatchers"])
    async def dextop(self, ctx):
        """Show this server's top collectors by total creatures caught."""
        rows = await db.top_collectors(ctx.guild.id, creature_names())
        embed = discord.Embed(title="🐾 Top Collectors", color=_CREATURE_COLOR)
        if not rows:
            embed.description = (
                "No one has been catching yet — be the first with `!catch`!"
            )
            await ctx.send(embed=embed)
            return
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for rank, (user_id, caught, unique) in enumerate(rows):
            prefix = medals[rank] if rank < len(medals) else f"**{rank + 1}.**"
            member = resources.resolve_member(ctx.guild, user_id)
            name = member.display_name if member else f"User {user_id}"
            lines.append(
                f"{prefix} {name} — **{caught}** caught "
                f"({unique}/{len(CREATURES)} creatures)",
            )
        embed.description = "\n".join(lines)
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------ help hook

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — a static creature overview.

        Creatures are hub-less (no persistent panel yet), so this returns a plain
        informational embed + an empty view (the Help framework's contract).
        """
        embed = discord.Embed(
            title="🐾 Creatures",
            description=(
                f"Catch from **{len(CREATURES)}** original creatures across "
                "six elements. Rarer creatures show up less often and are harder "
                "to catch — fill out your dex and battle other trainers.\n\n"
                "**`!catch`** — head into the wild\n"
                "**`!dex`** — your collection\n"
                "**`!dextop`** — the server leaderboard\n"
                "**`!cbattle @member`** — challenge a trainer to a "
                "level-normalized PvP battle\n"
                "**`!cbattletop`** — the PvP win ladder"
            ),
            color=INFO_COLOR,
        )
        return embed, discord.ui.View()


async def setup(bot):
    await bot.add_cog(CreatureCog(bot))
