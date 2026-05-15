from __future__ import annotations

import json
import os
import random

import discord
from core.runtime import panel_manager
from core.runtime.persistent_views import PersistentView, register
from discord.ext import commands
from utils import db
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR

RECIPES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "json",
    "recipes.json",
)


#
# ===== HELPER FUNCTIONS (Outside the Cog) =====
#


def load_recipes():
    """
    Loads build/crafting recipes from recipes.json.
    Falls back to a default dict if the file is missing/invalid.
    Ensures all keys are lowercase for consistency and skips invalid entries.
    """
    default_recipes = {
        "stone hut": {"stone": 5},
        "iron pickaxe": {"iron": 3, "wood": 1},
        "gold statue": {"gold": 4},
        "diamond throne": {"diamond": 6},
        "wooden house": {"wood": 8},
    }

    if not os.path.exists(RECIPES_FILE):
        return default_recipes

    try:
        with open(RECIPES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return default_recipes

            normalized = {}
            for recipe_name, requirements in data.items():
                if not isinstance(requirements, dict):
                    continue
                recipe_lower = recipe_name.lower()
                normalized_req = {}
                for mat, qty in requirements.items():
                    if isinstance(mat, str) and isinstance(qty, int):
                        normalized_req[mat.lower()] = qty
                if normalized_req:
                    normalized[recipe_lower] = normalized_req
            return normalized if normalized else default_recipes

    except (json.JSONDecodeError, ValueError):
        return default_recipes


#
# ===== THE COG CLASS =====
#


class MiningCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recipes = load_recipes()

    #
    # ====== INTERNAL HELPER METHOD ======
    #
    async def update_inventory(self, user_id, item, amount=1):
        """
        Updates a user's inventory by 'amount' of 'item'.
        Delegates to the DB helper which clamps to 0 automatically.
        """
        await db.update_mining_item(str(user_id), item, amount)

    #
    # ====== VIEW FOR MINING BUTTONS ======
    #
    class MineView(discord.ui.View):
        """Simple View for the !mine command: 'Mine Left', 'Mine Right', 'Mine Down'."""

        def __init__(self, user_id, cog):
            super().__init__(timeout=30)
            self.user_id = user_id
            self.cog = cog
            self.message: discord.Message | None = None

        async def interaction_check(self, interaction: discord.Interaction):
            return interaction.user.id == self.user_id

        async def on_timeout(self) -> None:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

        @discord.ui.button(label="Mine Left", style=discord.ButtonStyle.primary)
        async def mine_left(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            await self.handle_mine(interaction, "left")

        @discord.ui.button(label="Mine Right", style=discord.ButtonStyle.primary)
        async def mine_right(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            await self.handle_mine(interaction, "right")

        @discord.ui.button(label="Mine Down", style=discord.ButtonStyle.primary)
        async def mine_down(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            await self.handle_mine(interaction, "down")

        async def handle_mine(self, interaction: discord.Interaction, direction: str):
            await interaction.response.defer()

            user_id = str(self.user_id)
            inventory = await db.get_mining_inventory(user_id)
            pickaxe_bonus = 2 if inventory.get("pickaxe", 0) > 0 else 1
            # Weighted random resource
            ores = {"stone": 3, "iron": 2, "gold": 1, "diamond": 0.5}
            found = random.choices(list(ores.keys()), weights=list(ores.values()), k=1)[
                0
            ]
            amount = random.randint(1, 3) * pickaxe_bonus

            await self.cog.update_inventory(user_id, found, amount)

            new_content = f"{interaction.user.mention} mined {amount}x **{found}** by going {direction}!"
            await interaction.message.edit(content=new_content, embed=None, view=None)
            self.stop()

    #
    # ====== USER COMMANDS ======
    #

    @commands.command()
    async def minemenu(self, ctx):
        """Open the mining hub panel."""
        view = MiningHubView()
        await panel_manager.get_or_render_panel(ctx, "mining", view.build_embed(), view)

    @commands.command()
    async def mine(self, ctx):
        """Start mining with interactive buttons."""
        view = self.MineView(ctx.author.id, self)
        embed = discord.Embed(
            title="Mining",
            description="Choose a direction to mine.\nIf you own a pickaxe, you'll get extra loot!",
            color=MINING_COLOR,
        )
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(hidden=True)
    async def chop(self, ctx):
        """Chop wood. If you have an 'axe', you'll collect double."""
        user_id = str(ctx.author.id)
        inventory = await db.get_mining_inventory(user_id)
        multiplier = 2 if inventory.get("axe", 0) > 0 else 1
        wood_amount = random.randint(1, 3) * multiplier
        await self.update_inventory(ctx.author.id, "wood", wood_amount)
        await ctx.send(
            f"{ctx.author.mention} chopped wood and collected {wood_amount}x wood!"
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
        inventory = await db.get_mining_inventory(user_id)
        total_items = sum(inventory.values())
        unique_items = len(inventory)

        embed = discord.Embed(
            title=f"{ctx.author.name}'s Mining Stats", color=MINING_COLOR
        )
        embed.add_field(name="Total Items Collected", value=str(total_items))
        embed.add_field(name="Unique Items", value=str(unique_items))
        await ctx.send(embed=embed)

    #
    # ====== BUILD / CRAFTING COMMANDS ======
    #

    @commands.command(hidden=True)
    async def build(self, ctx, *, structure: str = None):
        """
        Build a structure based on recipes.
        If no structure is specified, calls !buildlist to show all.
        """
        try:
            if structure is None:
                return await ctx.invoke(self.bot.get_command("buildlist"))

            user_id = str(ctx.author.id)
            inventory = await db.get_mining_inventory(user_id)

            structure_lower = structure.lower()
            required_items = self.recipes.get(structure_lower)

            if not required_items:
                return await ctx.send(
                    "Unknown structure. Use `!buildlist` to see all available structures."
                )

            # Check resources
            for item, amount_needed in required_items.items():
                if inventory.get(item, 0) < amount_needed:
                    return await ctx.send(
                        f"You don't have enough **{item}** to build **{structure}**."
                    )

            # Subtract cost and give the user the new buildable item
            for item, amount_needed in required_items.items():
                await self.update_inventory(ctx.author.id, item, -amount_needed)
            await self.update_inventory(ctx.author.id, structure_lower, 1)

            await ctx.send(
                f"{ctx.author.mention} successfully built a **{structure}**!"
            )
        except Exception as e:
            print(f"[ERROR in build command]: {e}")
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
                    [f"{mat}: {amt}" for mat, amt in requirements.items()]
                )
                recipe_lines.append(f"**{structure_name.title()}**: Requires {req_str}")

            embed = discord.Embed(
                title="Available Structures",
                description="\n".join(recipe_lines),
                color=SUCCESS_COLOR,
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"[ERROR in buildlist command]: {e}")
            await ctx.send(
                "An unexpected error occurred while listing buildable structures."
            )

    @commands.command(hidden=True)
    async def buildable(self, ctx):
        """
        Lists only what the user can currently build based on their inventory.
        """
        user_id = str(ctx.author.id)
        inventory = await db.get_mining_inventory(user_id)

        can_build = []
        for structure_name, requirements in self.recipes.items():
            if all(inventory.get(item, 0) >= amt for item, amt in requirements.items()):
                can_build.append(structure_name)

        if not can_build:
            return await ctx.send(
                "You currently don't have enough resources to build anything."
            )

        embed = discord.Embed(
            title=f"{ctx.author.name}'s Buildable Structures",
            description="\n".join(s.title() for s in can_build),
            color=SUCCESS_COLOR,
        )
        await ctx.send(embed=embed)

    #
    # ====== OPTIONAL EXPLORATION / SPECIAL ITEMS ======
    #

    @commands.command(hidden=True)
    async def explore(self, ctx):
        """Discover random events or items."""
        user_id = str(ctx.author.id)
        outcomes = [
            "found 1 gold in an abandoned camp!",
            "stumbled upon a hidden diamond vein and got 1 diamond!",
            "was attacked by monsters and lost 2 stone...",
            "found a secret chest with 3 wood!",
            "got lost and found nothing...",
        ]
        result = random.choice(outcomes)

        if "found 1 gold" in result:
            await self.update_inventory(user_id, "gold", 1)
        elif "1 diamond" in result:
            await self.update_inventory(user_id, "diamond", 1)
        elif "lost 2 stone" in result:
            await self.update_inventory(user_id, "stone", -2)
        elif "3 wood" in result:
            await self.update_inventory(user_id, "wood", 3)

        await ctx.send(f"{ctx.author.mention} {result}")

    @commands.command(hidden=True)
    async def use(self, ctx, *, item: str = None):
        """Use a special item from your inventory (e.g., torch, dynamite)."""
        if not item:
            return await ctx.send("Please specify an item to use, e.g. `!use torch`.")

        user_id = str(ctx.author.id)
        item = item.lower()

        inventory = await db.get_mining_inventory(user_id)
        if inventory.get(item, 0) < 1:
            return await ctx.send(f"You don't have **{item}** to use.")

        if item == "torch":
            message = "You light a torch and peer into the darkness..."
        elif item == "dynamite":
            message = "You ignite dynamite and blow a new path in the mine!"
        else:
            message = f"You used **{item}**, but nothing special happened."

        await self.update_inventory(user_id, item, -1)
        await ctx.send(f"{ctx.author.mention} {message}")

    #
    # ====== ADMIN COMMANDS ======
    #

    @commands.command()
    async def reset_inventory(self, ctx, member: discord.Member):
        """Admin-only: reset a user's inventory."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("You don't have permission to do that.")

        await db.set_mining_inventory(str(member.id), {})
        await ctx.send(f"{member.name}'s inventory has been reset.")

    @commands.command()
    async def give(self, ctx, member: discord.Member, item: str, amount: int):
        """Admin-only: give resources to a user."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("You don't have permission to do that.")

        item = item.lower()
        await db.update_mining_item(str(member.id), item, amount)
        await ctx.send(f"Gave {amount}x **{item}** to {member.name}.")


#
# ===== SETUP FUNCTION =====
#


async def setup(bot):
    await bot.add_cog(MiningCog(bot))


# ---------------------------------------------------------------------------
# Mining Hub View
# ---------------------------------------------------------------------------


@register
class MiningHubView(PersistentView):
    """Persistent, stateless mining hub panel."""

    SUBSYSTEM = "mining"

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=(
                "**⛏️ Mine** — start a mining session\n"
                "**🌲 Harvest** — chop wood\n"
                "**🗺️ Explore** — discover random events\n"
                "**📦 Inventory** — view your mining resources\n"
                "**📊 Stats** — view your mining statistics\n"
                "**🔨 Build** — craft a structure"
            ),
            color=MINING_COLOR,
        )
        embed.set_footer(text="Only you can interact with this panel.")
        return embed

    @discord.ui.button(
        label="⛏️ Mine",
        style=discord.ButtonStyle.primary,
        custom_id="mining:mine",
        row=0,
    )
    async def mine_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        cog: MiningCog = interaction.client.cogs.get("MiningCog")
        view = MiningCog.MineView(interaction.user.id, cog)
        embed = discord.Embed(
            title="Mining",
            description="Choose a direction to mine.\nIf you own a pickaxe, you'll get extra loot!",
            color=MINING_COLOR,
        )
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message

    @discord.ui.button(
        label="🌲 Harvest",
        style=discord.ButtonStyle.primary,
        custom_id="mining:harvest",
        row=0,
    )
    async def harvest_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        cog: MiningCog = interaction.client.cogs.get("MiningCog")
        user_id = str(interaction.user.id)
        inventory = await db.get_mining_inventory(user_id)
        multiplier = 2 if inventory.get("axe", 0) > 0 else 1
        wood_amount = random.randint(1, 3) * multiplier
        await cog.update_inventory(user_id, "wood", wood_amount)
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=f"{interaction.user.mention} chopped wood and collected **{wood_amount}x wood**!",
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="🗺️ Explore",
        style=discord.ButtonStyle.primary,
        custom_id="mining:explore",
        row=0,
    )
    async def explore_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        cog: MiningCog = interaction.client.cogs.get("MiningCog")
        user_id = str(interaction.user.id)
        outcomes = [
            ("found 1 gold in an abandoned camp!", "gold", 1),
            ("stumbled upon a hidden diamond vein and got 1 diamond!", "diamond", 1),
            ("was attacked by monsters and lost 2 stone...", "stone", -2),
            ("found a secret chest with 3 wood!", "wood", 3),
            ("got lost and found nothing...", None, 0),
        ]
        text, item, amount = random.choice(outcomes)
        if item:
            await cog.update_inventory(user_id, item, amount)
        embed = discord.Embed(
            title="⛏️ Mining Hub",
            description=f"{interaction.user.mention} {text}",
            color=SUCCESS_COLOR if amount >= 0 else ERROR_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="📦 Inventory",
        style=discord.ButtonStyle.grey,
        custom_id="mining:inventory",
        row=1,
    )
    async def inventory_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ):
        user_id = str(interaction.user.id)
        inventory = await db.get_mining_inventory(user_id)
        if not inventory:
            description = "Your mining inventory is empty."
        else:
            description = "\n".join(
                f"**{item.title()}**: {qty}" for item, qty in sorted(inventory.items())
            )
        embed = discord.Embed(
            title=f"📦 {interaction.user.name}'s Mining Inventory",
            description=description,
            color=MINING_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="📊 Stats",
        style=discord.ButtonStyle.grey,
        custom_id="mining:stats",
        row=1,
    )
    async def stats_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        user_id = str(interaction.user.id)
        inventory = await db.get_mining_inventory(user_id)
        total_items = sum(inventory.values())
        unique_items = len(inventory)
        embed = discord.Embed(
            title=f"📊 {interaction.user.name}'s Mining Stats",
            color=MINING_COLOR,
        )
        embed.add_field(name="Total Items Collected", value=str(total_items))
        embed.add_field(name="Unique Items", value=str(unique_items))
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="🔨 Build",
        style=discord.ButtonStyle.grey,
        custom_id="mining:build",
        row=1,
    )
    async def build_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        cog: MiningCog = interaction.client.cogs.get("MiningCog")
        await interaction.response.send_modal(_BuildModal(cog))

    @discord.ui.button(
        label="↩ Overview",
        style=discord.ButtonStyle.secondary,
        custom_id="mining:overview",
        row=2,
    )
    async def overview_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ):
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


# ---------------------------------------------------------------------------
# Build Modal
# ---------------------------------------------------------------------------


class _BuildModal(discord.ui.Modal, title="Build a Structure"):  # type: ignore[call-arg]
    structure = discord.ui.TextInput(
        label="Structure name",
        placeholder="e.g. stone hut, iron pickaxe",
        max_length=100,
    )

    def __init__(self, cog: "MiningCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        structure_lower = self.structure.value.strip().lower()

        required_items = self.cog.recipes.get(structure_lower)
        if not required_items:
            await interaction.response.send_message(
                f"Unknown structure **{self.structure.value}**. Use `!buildlist` to see available structures.",
                ephemeral=True,
            )
            return

        inventory = await db.get_mining_inventory(user_id)
        for item, amount_needed in required_items.items():
            if inventory.get(item, 0) < amount_needed:
                await interaction.response.send_message(
                    f"You don't have enough **{item}** to build **{self.structure.value}**.",
                    ephemeral=True,
                )
                return

        for item, amount_needed in required_items.items():
            await self.cog.update_inventory(user_id, item, -amount_needed)
        await self.cog.update_inventory(user_id, structure_lower, 1)

        await interaction.response.send_message(
            f"{interaction.user.mention} successfully built a **{self.structure.value}**!",
            ephemeral=True,
        )
