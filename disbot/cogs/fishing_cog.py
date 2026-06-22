"""Fishing subsystem — Discord plumbing only (S4.1 decomposition).

Ecosystem #2 (the second character-platform activity), PR 1 — fishing v1 per the
owner's design (Q-0175, ``docs/planning/fishing-open-world-expansion-plan-2026-06-18.md``):
21 size-ranked fish, 7 levels × 3 fish (level-gated catch — your fishing level
unlocks bigger fish), leveling reuses ``game_xp``. Fish value/use is a deferred
owner question, so v1 has no coins — the reward is progression + the collection log.

Domain logic, the audited write boundary, and the data live in their own modules:

    utils/fishing/                 — pure domain (catalog, level-gated roll)
    services/fishing_workflow.py   — the audited write boundary
    utils/db/games/fishing.py      — the collection-log CRUD
    disbot/data/fishing/fish.json  — the 21-fish dataset

This file hosts only commands, the cog lifecycle, and the Help-menu hook.
Fishing is **hub-less** for PR 1 (surfaced via its Help hook + the typed
commands, like ``welcome``/``counters``); folding ``🎣 Fishing`` into the
open-world Explore hub (currently a stub) is a later plan slice.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import guild_resources as resources
from services import fishing_workflow, game_xp_service
from utils import db
from utils.fishing import rods as rods_mod
from utils.fishing.fish import MAX_LEVEL, SPECIES, max_size_rank_for_level
from utils.ui_constants import GAME_COLOR, INFO_COLOR
from views.fishing import (
    FishingCastView,
    RodShopView,
    active_casts,
    build_rod_embed,
)

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
        """Cast a line — wait for the bite, then reel it in before it gets away."""
        key = (ctx.author.id, ctx.guild.id)
        if key in active_casts:
            await ctx.send(
                "🎣 You've already got a line in the water — reel that one in first!",
            )
            return

        # The equipped rod tunes the cast (rarity-pull on the roll; window /
        # bite-speed / escape-resist in the view).
        rod = await fishing_workflow.get_rod(ctx.author.id, ctx.guild.id)
        # Roll the catch now (read-only) so the minigame knows what's biting;
        # the write happens only if the player reels it in (commit_catch).
        cast = await fishing_workflow.roll_cast(ctx.author.id, ctx.guild.id, rod)
        if cast.catch is None:
            await ctx.send("🎣 The fishing spot is unavailable right now — try later.")
            return

        view = FishingCastView(ctx.author.id, ctx.guild.id, cast, rod=rod)
        embed = discord.Embed(
            description=(
                f"{ctx.author.mention} casts a line… 🎣\n"
                "*Watch the water — hit **Reel** the moment it bites, "
                "but not before!*"
            ),
            color=GAME_COLOR,
        )
        view.message = await ctx.send(embed=embed, view=view)
        view.start()

    @commands.command(
        name="fishlog",
        aliases=["fishdex"],
    )
    async def fishlog(self, ctx):
        """Show your fishing collection — every species you've caught."""
        log = await db.get_fishing_log(ctx.author.id, ctx.guild.id)
        xp_map = await db.get_game_xp(ctx.author.id, ctx.guild.id)
        fishing_xp = xp_map.get(game_xp_service.GAME_FISHING, 0)
        level = fishing_workflow.fishing_level_from_xp(fishing_xp)
        cap = max_size_rank_for_level(level)

        # Count only current-catalog species — a player who fished under the
        # superseded interim catalog (Q-0175 reconciliation) may have legacy rows
        # (e.g. `golden koi`) that would otherwise show impossible progress (23/21).
        known = {s.name for s in SPECIES}
        caught = sum(1 for name in log if name in known)
        total = sum(c for name, c in log.items() if name in known)
        embed = discord.Embed(
            title=f"🎣 {ctx.author.display_name}'s Fishing Log",
            color=_FISHING_COLOR,
        )
        embed.description = (
            f"**{caught}/{len(SPECIES)}** species discovered · "
            f"**{total}** total catches · Fishing level **{level}/{MAX_LEVEL}** "
            f"(can catch up to size **#{cap}**)"
        )
        lines = []
        for species in SPECIES:
            count = log.get(species.name, 0)
            unlocked = species.size_rank <= cap
            if count:
                lines.append(
                    f"{species.emoji} **{species.name.title()}** "
                    f"(#{species.size_rank}) ×{count}",
                )
            elif unlocked:
                lines.append(
                    f"{species.emoji} {species.name.title()} (#{species.size_rank}) "
                    "— *not yet caught*",
                )
            else:
                lines.append(f"🔒 ??? (#{species.size_rank}) — *locked*")
        embed.add_field(name="Fish", value="\n".join(lines), inline=False)
        embed.set_footer(text="!fish to cast · !fishtop for the leaderboard")
        await ctx.send(embed=embed)

    @commands.command(
        name="fishtop",
        aliases=["topfishers"],
    )
    async def fishtop(self, ctx):
        """Show this server's top anglers by total fish caught."""
        rows = await db.top_fishers(ctx.guild.id, [s.name for s in SPECIES])
        embed = discord.Embed(title="🎣 Top Anglers", color=_FISHING_COLOR)
        if not rows:
            embed.description = (
                "No one has cast a line yet — be the first with `!fish`!"
            )
            await ctx.send(embed=embed)
            return
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for rank, (user_id, caught, species) in enumerate(rows):
            prefix = medals[rank] if rank < len(medals) else f"**{rank + 1}.**"
            member = resources.resolve_member(ctx.guild, user_id)
            name = member.display_name if member else f"User {user_id}"
            lines.append(
                f"{prefix} {name} — **{caught}** caught "
                f"({species}/{len(SPECIES)} species)",
            )
        embed.description = "\n".join(lines)
        await ctx.send(embed=embed)

    @commands.command(name="rod", aliases=["rodshop", "buyrod"])
    async def rod(self, ctx):
        """View your fishing rod and upgrade it for coins."""
        tier = await db.get_rod_tier(ctx.author.id, ctx.guild.id)
        current = rods_mod.rod_for_tier(tier)
        nxt = rods_mod.next_rod(tier)
        balance = await db.get_coins(ctx.author.id, ctx.guild.id)
        embed = build_rod_embed(current, nxt, balance)
        view = RodShopView(ctx.author, ctx.guild.id, at_max=nxt is None)
        view.message = await ctx.send(embed=embed, view=view)

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
                f"Cast a line to catch from **{len(SPECIES)}** size-ranked fish. "
                "Wait for the bite, reel it in, and fight the big ones. Level up to "
                "unlock bigger catches and buy better rods.\n\n"
                "**`!fish`** — cast a line (wait → bite → reel)\n"
                "**`!rod`** — view & upgrade your rod\n"
                "**`!fishlog`** — your collection\n"
                "**`!fishtop`** — the server leaderboard"
            ),
            color=INFO_COLOR,
        )
        return embed, discord.ui.View()


async def setup(bot):
    await bot.add_cog(FishingCog(bot))
