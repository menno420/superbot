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
from utils.fishing import bait as bait_mod
from utils.fishing import rods as rods_mod
from utils.fishing.fish import SPECIES
from views.fishing import (
    BaitShopView,
    FishingMenuView,
    RodShopView,
    build_bait_embed,
    build_fishlog_embed,
    build_menu_embed,
    build_rod_embed,
    prepare_cast,
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
        prepared = await prepare_cast(ctx.author.id, ctx.guild.id)
        if isinstance(prepared, str):
            await ctx.send(prepared)
            return
        embed, view = prepared
        view.message = await ctx.send(embed=embed, view=view)
        view.start()

    @commands.command(name="fishing", aliases=["fishmenu"])
    async def fishing(self, ctx):
        """Open the interactive fishing menu — cast, upgrade your rod, browse the dex."""
        energy = await fishing_workflow.get_energy(ctx.author.id, ctx.guild.id)
        profile = await fishing_workflow.get_venue(ctx.author.id, ctx.guild.id)
        view = FishingMenuView(ctx.author, ctx.guild.id)
        view.message = await ctx.send(
            embed=build_menu_embed(energy, profile),
            view=view,
        )

    @commands.command(name="sail", aliases=["setsail", "dock"])
    async def sail(self, ctx):
        """Set sail for deepwater (or dock back on shore) — toggles your fishing venue.

        Deepwater holds rare boat-only fish that bite slower and fight harder;
        shore is the relaxed everyday catch. Your choice persists, so ``!fish``
        casts wherever you last set sail to.
        """
        change = await fishing_workflow.toggle_venue(ctx.author.id, ctx.guild.id)
        await ctx.send(change.message)

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
        embed = build_fishlog_embed(ctx.author.display_name, log, level)
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

    @commands.command(name="bait", aliases=["baitshop", "buybait"])
    async def bait(self, ctx):
        """Load fishing bait — a consumable that pulls catches toward bigger fish."""
        active, charges = await fishing_workflow.get_active_bait(
            ctx.author.id,
            ctx.guild.id,
        )
        balance = await db.get_coins(ctx.author.id, ctx.guild.id)
        embed = build_bait_embed(active, charges, balance)
        view = BaitShopView(ctx.author, ctx.guild.id)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="craftbait", aliases=["baitcraft"])
    async def craftbait(self, ctx, *, bait: str = ""):
        """Craft bait from small caught fish — closes the catch→bait loop.

        With a bait name (e.g. ``!craftbait worm``) crafts that pack directly;
        with no argument, opens the bait panel where the Craft select lists the
        recipes. Only the cheaper / mid baits are craftable.
        """
        key = bait_mod.craftable_key_for(bait)
        if not bait:
            await self.bait(ctx)
            return
        if key is None:
            craftable = ", ".join(
                bait_mod.bait_by_key(k).name  # type: ignore[union-attr]
                for k in bait_mod.CRAFTABLE_KEYS
            )
            await ctx.send(
                f"You can't craft **{bait}** from fish. Craftable: {craftable}.",
            )
            return
        result = await fishing_workflow.craft_bait(ctx.author.id, ctx.guild.id, key)
        await ctx.send(result.message)

    # ------------------------------------------------------------------ help hook

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — the interactive fishing panel.

        Returns the live :class:`FishingMenuView` (🎣 Cast · 🎒 Rod · 📖 Fishdex)
        so the menu is actionable in place, not a static overview.
        """
        energy = await fishing_workflow.get_energy(
            interaction.user.id,
            interaction.guild.id,
        )
        profile = await fishing_workflow.get_venue(
            interaction.user.id,
            interaction.guild.id,
        )
        return build_menu_embed(energy, profile), FishingMenuView(
            interaction.user,
            interaction.guild.id,
        )


async def setup(bot):
    await bot.add_cog(FishingCog(bot))
