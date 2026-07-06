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
from utils.fishing import CORAL_ITEM, PEARL_ITEM
from utils.fishing import bait as bait_mod
from utils.fishing import curios as curios_mod
from utils.fishing import gear as fishing_gear
from utils.fishing import rods as rods_mod
from utils.fishing import weather as weather_mod
from utils.fishing.fish import SPECIES, fish_names, species_by_name
from views.fishing import (
    BaitShopView,
    BoathouseView,
    DockView,
    FisheryView,
    FishingMenuView,
    RodShopView,
    TidePoolView,
    build_bait_embed,
    build_boathouse_embed,
    build_dock_embed,
    build_fishery_embed,
    build_fishlog_embed,
    build_menu_embed,
    build_recipe_panel,
    build_rod_embed,
    build_tide_pool_embed,
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

    @commands.command(name="forecast", aliases=["fishforecast", "fishingweather"])
    async def forecast(self, ctx):
        """Show today's fishing forecast — the date-seeded weather everyone shares.

        Weather biases every cast for the day (faster/slower bites, rarer fish);
        it's the same for everyone, so it's a shared reason to fish *today*.
        """
        w = fishing_workflow.get_forecast()
        embed = discord.Embed(
            title=f"{w.emoji} Today's fishing forecast: {w.name}",
            description=(
                f"{w.blurb}\n\n**Effect on every cast:** {weather_mod.effect_text(w)}"
            ),
            color=_FISHING_COLOR,
        )
        embed.set_footer(text="Same for everyone today · 🎣 !fish to cast")
        await ctx.send(embed=embed)

    @commands.command(name="sail", aliases=["setsail"])
    async def sail(self, ctx):
        """Set sail for deepwater (or return to shore) — toggles your fishing venue.

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
        records = await db.get_fishing_records(ctx.author.id, ctx.guild.id)
        xp_map = await db.get_game_xp(ctx.author.id, ctx.guild.id)
        fishing_xp = xp_map.get(game_xp_service.GAME_FISHING, 0)
        level = fishing_workflow.fishing_level_from_xp(fishing_xp)
        embed = build_fishlog_embed(ctx.author.display_name, log, level, records)
        await ctx.send(embed=embed)

    @commands.command(
        name="fishtop",
        aliases=["topfishers"],
    )
    async def fishtop(self, ctx):
        """Show this server's top anglers by total fish caught."""
        rows = await db.top_fishers(ctx.guild.id, fish_names())
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

    @commands.command(
        name="trophies",
        aliases=["bigfish", "fishtrophy"],
    )
    async def trophies(self, ctx):
        """Show this server's heaviest catches — the biggest-fish hall of fame."""
        rows = await db.top_trophies(ctx.guild.id, fish_names())
        embed = discord.Embed(title="🏅 Biggest Catches", color=_FISHING_COLOR)
        if not rows:
            embed.description = (
                "No trophies landed yet — reel in a big one with `!fish`!"
            )
            await ctx.send(embed=embed)
            return
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for rank, (user_id, species, weight) in enumerate(rows):
            prefix = medals[rank] if rank < len(medals) else f"**{rank + 1}.**"
            member = resources.resolve_member(ctx.guild, user_id)
            name = member.display_name if member else f"User {user_id}"
            fish = species_by_name(species)
            emoji = fish.emoji if fish else "🐟"
            lines.append(
                f"{prefix} {emoji} **{weight:g} kg** {species.title()} — {name}",
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
        inventory = await db.get_mining_inventory(str(ctx.author.id), ctx.guild.id)
        pearls = inventory.get(PEARL_ITEM, 0)
        embed = build_bait_embed(active, charges, balance, pearls=pearls)
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

    @commands.command(name="craftcharm", aliases=["charmcraft"])
    async def craftcharm(self, ctx, *, charm: str = ""):
        """Craft a fishing charm from caught fish — the non-coin earn path.

        With a charm name (e.g. ``!craftcharm fishing charm``) crafts it directly
        from your small caught fish; with no argument, lists the craftable charms
        and their fish cost. Charms also sell for coins in the gear shop
        (``!gear``) — crafting is the slower, gameplay-native alternative.
        """
        name = fishing_gear.craftable_charm_for(charm)
        if not charm or name is None:
            lines = [
                f"🎣 **{r.charm.title()}** — {fishing_gear.charm_recipe_text(r)}"
                for r in fishing_gear.CHARM_RECIPES.values()
            ]
            prefix = (
                f"You can't craft **{charm}** from fish.\n"
                if charm
                else "Craft a fishing charm from caught fish "
                "(or buy one with `!gear`):\n"
            )
            await ctx.send(prefix + "\n".join(lines))
            return
        result = await fishing_workflow.craft_charm(ctx.author.id, ctx.guild.id, name)
        await ctx.send(result.message)

    @commands.command(name="craftrod", aliases=["rodcraft"])
    async def craftrod(self, ctx):
        """Craft the next rod up the ladder from caught fish — the non-coin path.

        Crafts the next rod tier from your small caught fish (smallest-first),
        exactly like ``!craftcharm``. Rods also sell for coins in the rod shop
        (``!rod``) — crafting is the slower, gameplay-native alternative.
        """
        result = await fishing_workflow.craft_rod(ctx.author.id, ctx.guild.id)
        await ctx.send(result.message)

    @commands.command(name="rodrecipes", aliases=["rodrecipe", "rrecipes"])
    async def rodrecipes(self, ctx):
        """Browse every fish→rod recipe and your live progress toward each tier."""
        embed, view = await build_recipe_panel(ctx.author, ctx.guild.id)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="craftpearl", aliases=["pearlcraft"])
    async def craftpearl(self, ctx, *, bait: str = ""):
        """Spend pearls to craft the premium bait — the rare-material sink.

        Pearls drop rarely when you reel in a fish (bigger fish, better odds).
        With a bait name (e.g. ``!craftpearl feast``) crafts it directly; with no
        argument, crafts the only pearl recipe — the premium **Royal Feast** bait
        (the one bait you can't craft from fish). Coins stay the fast alternative
        via ``!bait``.
        """
        key = bait_mod.pearl_craftable_key_for(bait)
        if not bait and len(bait_mod.PEARL_CRAFTABLE_KEYS) == 1:
            key = bait_mod.PEARL_CRAFTABLE_KEYS[0]
        if key is None:
            craftable = ", ".join(
                bait_mod.bait_by_key(k).name  # type: ignore[union-attr]
                for k in bait_mod.PEARL_CRAFTABLE_KEYS
            )
            await ctx.send(
                f"You can't craft **{bait}** from pearls. Pearl-craftable: "
                f"{craftable}.",
            )
            return
        result = await fishing_workflow.craft_pearl_bait(
            ctx.author.id,
            ctx.guild.id,
            key,
        )
        await ctx.send(result.message)

    @commands.command(name="curios", aliases=["curio", "carvings"])
    async def curios(self, ctx):
        """Show the coral-carving collection + your coral and craft progress.

        Coral drops rarely when you reel in a fish out in **deepwater** (`!sail`).
        Carve it into cosmetic curios with `!craftcurio <name>` — a completionist
        shelf, purely for show (never sold, no gameplay effect).
        """
        inventory = await db.get_mining_inventory(str(ctx.author.id), ctx.guild.id)
        coral = inventory.get(CORAL_ITEM, 0)
        owned, total = curios_mod.collection_progress(inventory)
        embed = discord.Embed(
            title="🪸 Coral Curios",
            description=(
                f"You have **{coral}** 🪸 coral · collection **{owned}/{total}** carved.\n"
                "Coral drops rarely on a **deepwater** reel (`!sail` to the boat)."
            ),
            color=_FISHING_COLOR,
        )
        for curio in curios_mod.CURIO_CATALOG:
            have = inventory.get(curio.item, 0)
            mark = "✅" if have > 0 else ("🔨" if coral >= curio.coral_cost else "🔒")
            owned_txt = f" ×{have}" if have > 0 else ""
            embed.add_field(
                name=f"{mark} {curio.emoji} {curio.name}{owned_txt}",
                value=f"{curios_mod.cost_text(curio)} · {curio.rarity}",
                inline=False,
            )
        embed.set_footer(text="Carve with !craftcurio <name>")
        await ctx.send(embed=embed)

    @commands.command(name="tidepool", aliases=["reef", "tidepools"])
    async def tidepool(self, ctx):
        """Build a Tide Pool — the deepwater-coral structure that pulls rarer catches.

        Coral drops rarely on a **deepwater** reel (`!sail`). Stock a reef pool with
        it to bias every cast toward the big end of your unlocked band — coral's
        *functional* sink alongside the cosmetic curios (`!curios`).
        """
        embed = await build_tide_pool_embed(ctx.author.id, ctx.guild.id)
        view = TidePoolView(ctx.author, ctx.guild.id)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="dock", aliases=["pier", "fishingdock"])
    async def dock(self, ctx):
        """Build a Dock — the cheap coral+wood structure that makes fish bite faster.

        The Tide Pool's sibling: coral drops on a **deepwater** reel (`!sail`) and
        wood you already mine. Faster bites (Dock) vs. rarer fish (`!tidepool`) —
        spend your coral where you like.
        """
        embed = await build_dock_embed(ctx.author.id, ctx.guild.id)
        view = DockView(ctx.author, ctx.guild.id)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="boathouse", aliases=["moorings", "boat"])
    async def boathouse(self, ctx):
        """Build a Boathouse — the coral+wood structure that refills energy faster.

        The third coral structure: coral drops on a **deepwater** reel (`!sail`) and
        wood you already mine. More fishing (Boathouse) vs. rarer fish (`!tidepool`)
        vs. faster bites (`!dock`) — spend your coral where you like.
        """
        embed = await build_boathouse_embed(ctx.author.id, ctx.guild.id)
        view = BoathouseView(ctx.author, ctx.guild.id)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="fishery", aliases=["hatchery", "fishfarm"])
    async def fishery(self, ctx):
        """Build a Fishery — the coral+wood structure that lands more double catches.

        The fourth coral structure: coral drops on a **deepwater** reel (`!sail`) and
        wood you already mine. A well-stocked fishery means a landed reel is likelier
        to hook a **second** fish. More fish per catch (Fishery) vs. rarer fish
        (`!tidepool`) vs. faster bites (`!dock`) vs. faster energy (`!boathouse`).
        """
        embed = await build_fishery_embed(ctx.author.id, ctx.guild.id)
        view = FisheryView(ctx.author, ctx.guild.id)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="craftcurio", aliases=["carve", "curiocraft"])
    async def craftcurio(self, ctx, *, curio: str = ""):
        """Carve a cosmetic curio from coral — the deepwater rare-material sink.

        Coral drops rarely when you reel in a fish out in **deepwater** (`!sail`).
        Name a curio (e.g. `!craftcurio coral idol`); with no argument it lists the
        collection. See `!curios` for your coral and progress.
        """
        key = curios_mod.craftable_key_for(curio)
        if key is None:
            craftable = ", ".join(c.name for c in curios_mod.CURIO_CATALOG)
            await ctx.send(
                f"That isn't a carvable curio. Carvable: {craftable}. "
                "See `!curios` for your collection.",
            )
            return
        result = await fishing_workflow.craft_curio(
            ctx.author.id,
            ctx.guild.id,
            key,
        )
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
