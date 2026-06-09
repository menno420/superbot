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

from cogs.mining import equipment, world
from cogs.mining.exploration import explore_from_state
from cogs.mining.items import total_value
from cogs.mining.recipes import load_recipes
from core.runtime import panel_manager
from utils import db
from utils.ui_constants import MINING_COLOR, SUCCESS_COLOR

# Pattern B re-export: importing this triggers @register on MiningHubView
# so message_anchor_manager.restore_anchors() finds the class at on_ready.
from views.mining import MineView, MiningHubView  # noqa: F401 — re-exported

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
        await panel_manager.get_or_render_panel(ctx, "mining", view.build_embed(), view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the mining hub panel)."""
        view = MiningHubView()
        return view.build_embed(), view

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

    @commands.command(hidden=True)
    async def build(self, ctx, *, structure: str = None):
        """Build a structure based on recipes.

        If no structure is specified, calls !buildlist to show all.
        """
        try:
            if structure is None:
                return await ctx.invoke(self.bot.get_command("buildlist"))

            user_id = str(ctx.author.id)
            gid = ctx.guild.id
            inventory = await db.get_mining_inventory(user_id, gid)

            structure_lower = structure.lower()
            required_items = self.recipes.get(structure_lower)

            if not required_items:
                return await ctx.send(
                    "Unknown structure. Use `!buildlist` to see all available structures.",
                )

            for item, amount_needed in required_items.items():
                if inventory.get(item, 0) < amount_needed:
                    return await ctx.send(
                        f"You don't have enough **{item}** to build **{structure}**.",
                    )

            for item, amount_needed in required_items.items():
                await self.update_inventory(
                    ctx.author.id,
                    gid,
                    item,
                    -amount_needed,
                )
            await self.update_inventory(ctx.author.id, gid, structure_lower, 1)

            await ctx.send(
                f"{ctx.author.mention} successfully built a **{structure}**!",
            )
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
        await ctx.send(
            f"{ctx.author.mention} {text}\n_{world.describe_position(depth)}_",
        )

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
        """Show your equipped gear and the stats it grants."""
        user_id = str(ctx.author.id)
        equipped = await db.get_equipment(user_id, ctx.guild.id)
        stats = equipment.compute_stats(equipped)
        embed = discord.Embed(
            title=f"🧍 {ctx.author.name}'s Gear",
            color=MINING_COLOR,
        )
        for slot in equipment.SLOTS:
            held = equipped.get(slot)
            embed.add_field(
                name=slot.title(),
                value=f"**{held.title()}**" if held else "*(empty)*",
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
