"""Mining subsystem — Discord plumbing only (S4.1 decomposition).

Domain logic, UI components, and modals have moved to their own
modules per ``docs/architecture.md`` §"Subsystem decomposition":

    cogs/mining/recipes.py      — JSON recipe loader
    cogs/mining/rewards.py      — loot tables (pure functions)
    views/mining/mine_view.py   — !mine ephemeral 3-button view
    views/mining/main_panel.py  — MiningHubView (PersistentView) + _BuildModal

This file hosts only commands, the cog lifecycle, and the
help-menu hook.  ``MiningHubView`` is imported below so the
``@register`` side-effect populates the persistent-view registry at
cog-load time (Pattern B per §"PersistentView placement").
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from cogs.mining import market, workshop, world
from cogs.mining.exploration import explore_from_state
from cogs.mining.items import total_value
from cogs.mining.recipes import load_recipes
from core.runtime import panel_manager
from utils import db, equipment
from utils.ui_constants import MINING_COLOR, SUCCESS_COLOR

# Pattern B re-export: importing this triggers @register on MiningHubView
# so message_anchor_manager.restore_anchors() finds the class at on_ready.
from views.mining import MineView, MiningHubView  # noqa: F401 — re-exported
from views.mining.main_panel import build_overview_embed

logger = logging.getLogger("bot.cogs.mining")


class MiningCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recipes = load_recipes()

    # PR M3: mining commands require a guild context.
    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    async def update_inventory(
        self,
        user_id,
        guild_id: int,
        item,
        amount: int = 1,
    ) -> None:
        """Delegate to the DB CRUD helper (S4.1 retained for command paths)."""
        await db.update_mining_item(str(user_id), guild_id, item, amount)

    # ------------------------------------------------------------------ commands

    @commands.command()
    async def minemenu(self, ctx):
        """Open the mining hub panel."""
        view = MiningHubView()
        embed = await build_overview_embed(
            ctx.author.id,
            ctx.guild.id,
            name=ctx.author.display_name,
        )
        await panel_manager.get_or_render_panel(ctx, "mining", embed, view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the mining hub panel).

        The live overview is an enrichment: navigation must not crash if its
        reads fail, so any error degrades to the stateless hub embed.
        """
        view = MiningHubView()
        if interaction.guild_id is None:
            return view.build_embed(), view
        try:
            embed = await build_overview_embed(
                interaction.user.id,
                interaction.guild_id,
                name=interaction.user.display_name,
            )
        except Exception:  # noqa: BLE001 — navigation must not crash Help
            logger.warning("mining overview unavailable; using static hub embed")
            return view.build_embed(), view
        return embed, view

    @commands.command()
    async def mine(self, ctx):
        """Start mining with interactive buttons."""
        view = MineView(ctx.author.id, ctx.guild.id)
        embed = discord.Embed(
            title="Mining",
            description=(
                "Choose a direction to mine.\n"
                "If you own a pickaxe, you'll get extra loot!"
            ),
            color=MINING_COLOR,
        )
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(hidden=True)
    async def chop(self, ctx):
        """Chop wood. If you have an 'axe', you'll collect double."""
        from cogs.mining.rewards import roll_harvest_amount

        user_id = str(ctx.author.id)
        inventory = await db.get_mining_inventory(user_id, ctx.guild.id)
        wood_amount = roll_harvest_amount(has_axe=inventory.get("axe", 0) > 0)
        await self.update_inventory(ctx.author.id, ctx.guild.id, "wood", wood_amount)
        await ctx.send(
            f"{ctx.author.mention} chopped wood and collected {wood_amount}x wood!",
        )

    @commands.command(name="mineinv", aliases=["mineinventory"], hidden=True)
    async def mineinv(self, ctx):
        """Show your unified inventory (compatibility alias for !inventory)."""
        cmd = ctx.bot.get_command("inventory")
        if cmd:
            await ctx.invoke(cmd)
        else:
            await ctx.send("❌ Inventory system not loaded.", delete_after=10)

    @commands.command(name="minestats", hidden=True)
    async def stats(self, ctx):
        """Shows your total mining items and number of unique items."""
        user_id = str(ctx.author.id)
        inventory = await db.get_mining_inventory(user_id, ctx.guild.id)
        total_items = sum(inventory.values())
        unique_items = len(inventory)

        depth = await db.get_depth(user_id, ctx.guild.id)
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Mining Stats",
            color=MINING_COLOR,
        )
        embed.add_field(
            name="Location",
            value=world.describe_position(depth),
            inline=False,
        )
        embed.add_field(name="Total Items Collected", value=str(total_items))
        embed.add_field(name="Unique Items", value=str(unique_items))
        embed.add_field(name="Net Worth", value=str(total_value(inventory)))
        await ctx.send(embed=embed)

    # ---------------------------------------------------------- build / crafting

    @commands.command(hidden=True, aliases=["craft"])
    async def build(self, ctx, *, structure: str = None):
        """Build / craft an item from recipes (one shared, atomic implementation).

        If no structure is specified, calls !buildlist to show all.
        """
        try:
            if structure is None:
                return await ctx.invoke(self.bot.get_command("buildlist"))
            result = await workshop.apply_craft(ctx.author.id, ctx.guild.id, structure)
            await ctx.send(f"{ctx.author.mention} {result.message}")
        except Exception:
            logger.exception("build command failed")
            await ctx.send("An unexpected error occurred while trying to build.")

    @commands.command(hidden=True)
    async def buildlist(self, ctx):
        """Shows all craftable structures from recipes.json."""
        try:
            if not self.recipes:
                return await ctx.send("No recipes available at this time.")

            recipe_lines = []
            for structure_name, requirements in self.recipes.items():
                if not isinstance(requirements, dict):
                    continue
                req_str = ", ".join(
                    [f"{mat}: {amt}" for mat, amt in requirements.items()],
                )
                recipe_lines.append(f"**{structure_name.title()}**: Requires {req_str}")

            embed = discord.Embed(
                title="Available Structures",
                description="\n".join(recipe_lines),
                color=SUCCESS_COLOR,
            )
            await ctx.send(embed=embed)
        except Exception:
            logger.exception("buildlist command failed")
            await ctx.send(
                "An unexpected error occurred while listing buildable structures.",
            )

    @commands.command(hidden=True)
    async def buildable(self, ctx):
        """Lists only what the user can currently build based on their inventory."""
        user_id = str(ctx.author.id)
        inventory = await db.get_mining_inventory(user_id, ctx.guild.id)

        can_build = []
        for structure_name, requirements in self.recipes.items():
            if all(inventory.get(item, 0) >= amt for item, amt in requirements.items()):
                can_build.append(structure_name)

        if not can_build:
            return await ctx.send(
                "You currently don't have enough resources to build anything.",
            )

        embed = discord.Embed(
            title=f"{ctx.author.name}'s Buildable Structures",
            description="\n".join(s.title() for s in can_build),
            color=SUCCESS_COLOR,
        )
        await ctx.send(embed=embed)

    # ---------------------------------------------------------- explore / use

    @commands.command(hidden=True)
    async def explore(self, ctx):
        """Discover random events or items (driven by your gear and depth)."""
        user_id = str(ctx.author.id)
        gid = ctx.guild.id
        inventory = await db.get_mining_inventory(user_id, gid)
        equipped = await db.get_equipment(user_id, gid)
        depth = await db.get_depth(user_id, gid)
        text, item, amount = explore_from_state(
            equipped,
            inventory,
            biome=world.biome_for_depth(depth),
        )
        if item:
            await self.update_inventory(user_id, gid, item, amount)
        wear = await workshop.apply_wear(
            ctx.author.id,
            gid,
            action=workshop.ACTION_EXPLORE,
            depth=depth,
            equipped=equipped,
        )
        message = f"{ctx.author.mention} {text}\n_{world.describe_position(depth)}_"
        if wear.notes:
            message += "\n" + "\n".join(wear.notes)
        await ctx.send(message)

    @commands.command(hidden=True)
    async def use(self, ctx, *, item: str = None):
        """Use a special item from your inventory (e.g., torch, dynamite)."""
        if not item:
            return await ctx.send("Please specify an item to use, e.g. `!use torch`.")

        user_id = str(ctx.author.id)
        gid = ctx.guild.id
        item = item.lower()

        inventory = await db.get_mining_inventory(user_id, gid)
        if inventory.get(item, 0) < 1:
            return await ctx.send(f"You don't have **{item}** to use.")

        if item == "torch":
            message = "You light a torch and peer into the darkness..."
        elif item == "dynamite":
            message = "You ignite dynamite and blow a new path in the mine!"
        else:
            message = f"You used **{item}**, but nothing special happened."

        await self.update_inventory(user_id, gid, item, -1)
        await ctx.send(f"{ctx.author.mention} {message}")

    # ---------------------------------------------------------- gear / equipment

    @commands.command(hidden=True)
    async def equip(self, ctx, *, item: str = None):
        """Equip a tool, light, or charm so its stats apply to your character."""
        if not item:
            return await ctx.send("Specify what to equip, e.g. `!equip iron pickaxe`.")
        item = item.strip().lower()
        slot = equipment.slot_for(item)
        if slot is None:
            return await ctx.send(f"**{item.title()}** can't be equipped.")
        user_id = str(ctx.author.id)
        gid = ctx.guild.id
        inventory = await db.get_mining_inventory(user_id, gid)
        if inventory.get(item, 0) < 1:
            return await ctx.send(f"You don't own a **{item.title()}** to equip.")
        await db.equip_item(user_id, gid, slot, item)
        await ctx.send(
            f"{ctx.author.mention} equipped **{item.title()}** in the **{slot}** slot.",
        )

    @commands.command(hidden=True)
    async def unequip(self, ctx, *, slot: str = None):
        """Clear an equipment slot (tool / light / charm)."""
        if not slot:
            return await ctx.send(
                f"Specify a slot to clear: {', '.join(equipment.SLOTS)}.",
            )
        slot = slot.strip().lower()
        if slot not in equipment.SLOTS:
            return await ctx.send(
                f"Unknown slot **{slot}**. Slots: {', '.join(equipment.SLOTS)}.",
            )
        await db.unequip_slot(str(ctx.author.id), ctx.guild.id, slot)
        await ctx.send(f"{ctx.author.mention} cleared the **{slot}** slot.")

    @commands.command(hidden=True)
    async def gear(self, ctx):
        """Show your equipped gear, its condition, and the stats it grants."""
        user_id = str(ctx.author.id)
        equipped = await db.get_equipment(user_id, ctx.guild.id)
        wear = await db.get_gear_wear(user_id, ctx.guild.id)
        stats = equipment.compute_stats(equipped)
        embed = discord.Embed(
            title=f"🧍 {ctx.author.name}'s Gear",
            color=MINING_COLOR,
        )
        for slot in equipment.SLOTS:
            held = equipped.get(slot)
            value = "*(empty)*"
            if held:
                value = f"**{held.title()}**"
                maximum = equipment.max_durability(held)
                if maximum is not None:
                    value += (
                        f"\n{workshop.durability_bar(wear.get(held, maximum), maximum)}"
                    )
            embed.add_field(
                name=slot.title(),
                value=value,
                inline=True,
            )
        bonuses = equipment.describe_stats(stats)
        embed.add_field(
            name="Stats",
            value=(
                "\n".join(f"{label}: +{value}" for label, value in bonuses)
                if bonuses
                else "No bonuses yet — equip some gear!"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="character", aliases=["profile", "char"], hidden=True)
    async def character(self, ctx):
        """Show your full mining character — location, gear, stats, wealth."""
        # cogs→views is allowed; the builder aggregates the existing owners.
        from views.mining.character_panel import build_character_embed

        embed = await build_character_embed(
            ctx.author.id,
            ctx.guild.id,
            name=ctx.author.display_name,
        )
        await ctx.send(embed=embed)

    # ---------------------------------------------------------- world / descent

    @commands.command(hidden=True)
    async def descend(self, ctx):
        """Descend one mining band deeper (gated by your equipped light)."""
        user_id = str(ctx.author.id)
        gid = ctx.guild.id
        depth = await db.get_depth(user_id, gid)
        stats = equipment.compute_stats(await db.get_equipment(user_id, gid))
        new_depth = world.descend(depth, stats)
        if new_depth == depth:
            await ctx.send(
                f"{ctx.author.mention} can't descend any deeper. "
                f"{world.descend_hint(stats)}",
            )
            return
        await db.set_depth(user_id, gid, new_depth)
        await ctx.send(
            f"{ctx.author.mention} descended to {world.describe_position(new_depth)}.",
        )

    @commands.command(hidden=True)
    async def ascend(self, ctx):
        """Climb one mining band back toward the surface."""
        user_id = str(ctx.author.id)
        gid = ctx.guild.id
        depth = await db.get_depth(user_id, gid)
        new_depth = world.ascend(depth)
        if new_depth == depth:
            await ctx.send(f"{ctx.author.mention} is already at the Surface.")
            return
        await db.set_depth(user_id, gid, new_depth)
        await ctx.send(
            f"{ctx.author.mention} climbed up to {world.describe_position(new_depth)}.",
        )

    # ---------------------------------------------------------- market

    @commands.command(hidden=True)
    async def sell(self, ctx, item: str = None, amount: int = 1):
        """Sell raw resources for coins (e.g. `!sell diamond 5`)."""
        if not item:
            return await ctx.send(
                "Specify what to sell, e.g. `!sell iron 10` — or `!sellall`.",
            )
        result = await market.apply_sell(ctx.author.id, ctx.guild.id, item, amount)
        await ctx.send(f"{ctx.author.mention} {result.message}")

    @commands.command(name="sellall", hidden=True)
    async def sell_all(self, ctx):
        """Sell every raw resource in your inventory for coins."""
        result = await market.apply_sell_all(ctx.author.id, ctx.guild.id)
        await ctx.send(f"{ctx.author.mention} {result.message}")

    @commands.command(hidden=True)
    async def buy(self, ctx, *, item: str = None):
        """Buy gear with coins (e.g. `!buy iron sword`)."""
        if not item:
            return await ctx.send("Specify what to buy — see `!market` for the shop.")
        result = await market.apply_buy(ctx.author.id, ctx.guild.id, item)
        await ctx.send(f"{ctx.author.mention} {result.message}")

    @commands.command(name="market", hidden=True)
    async def market_cmd(self, ctx):
        """Show the mining market — sellable resources + the gear shop."""
        inventory = await db.get_mining_inventory(str(ctx.author.id), ctx.guild.id)
        balance = await db.get_coins(ctx.author.id, ctx.guild.id)
        sellables = market.sellable_inventory(inventory)
        sale_total = sum(qty * price for _, qty, price in sellables)
        embed = discord.Embed(title="🛒 Mining Market", color=MINING_COLOR)
        if sellables:
            embed.add_field(
                name=f"💰 Sell (total {sale_total} 🪙)",
                value="\n".join(
                    f"**{name.title()}** ×{qty} → {qty * price} 🪙"
                    for name, qty, price in sellables
                ),
                inline=False,
            )
        embed.add_field(
            name="🛍️ Buy gear",
            value="\n".join(
                f"**{name.title()}** — {price} 🪙"
                for name, price in market.shop_listing()
            ),
            inline=False,
        )
        embed.set_footer(
            text=f"Balance: {balance} 🪙  •  !sell <item> [n] · !sellall · !buy <item>",
        )
        await ctx.send(embed=embed)

    # ---------------------------------------------------------- workshop

    @commands.command(name="workshop", hidden=True)
    async def workshop_cmd(self, ctx):
        """Open the workshop — repair worn gear, craft replacements."""
        # cogs→views is allowed; one builder shared with the hub button.
        from views.mining.workshop_panel import (
            MiningWorkshopView,
            build_workshop_embed,
        )

        embed = await build_workshop_embed(ctx.author.id, ctx.guild.id)
        view = await MiningWorkshopView.create(ctx.author, ctx.guild.id)
        await ctx.send(embed=embed, view=view)

    @commands.command(hidden=True)
    async def repair(self, ctx, *, item: str = None):
        """Repair a worn gear item for coins (e.g. `!repair pickaxe`)."""
        if not item:
            return await ctx.send(
                "Specify what to repair, e.g. `!repair pickaxe` — or `!workshop`.",
            )
        result = await workshop.apply_repair(ctx.author.id, ctx.guild.id, item)
        await ctx.send(f"{ctx.author.mention} {result.message}")

    @commands.command(name="quickcraft", hidden=True)
    async def quick_craft(self, ctx):
        """Re-craft the last gear item that broke and equip it."""
        result = await workshop.apply_quick_craft(ctx.author.id, ctx.guild.id)
        await ctx.send(f"{ctx.author.mention} {result.message}")

    # ---------------------------------------------------------------- admin

    @commands.command()
    async def reset_inventory(self, ctx, member: discord.Member):
        """Admin-only: reset a user's inventory in THIS guild (PR M3 — guild-scoped)."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("You don't have permission to do that.")

        await db.set_mining_inventory(str(member.id), ctx.guild.id, {})
        await ctx.send(f"{member.name}'s inventory has been reset.")

    @commands.command()
    async def give(self, ctx, member: discord.Member, item: str, amount: int):
        """Admin-only: give resources to a user."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("You don't have permission to do that.")

        item = item.lower()
        await db.update_mining_item(str(member.id), ctx.guild.id, item, amount)
        await ctx.send(f"Gave {amount}x **{item}** to {member.name}.")


async def setup(bot):
    await bot.add_cog(MiningCog(bot))
