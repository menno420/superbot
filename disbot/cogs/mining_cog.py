import discord
from discord.ext import commands
import random
import json
import os

DATA_DIR = "/home/menno/disbot/data/json"
DATA_FILE = os.path.join(DATA_DIR, "mining_data.json")
RECIPES_FILE = os.path.join(DATA_DIR, "recipes.json")


#
# ===== HELPER FUNCTIONS (Outside the Cog) =====
#

def load_data():
    """Loads mining data from the JSON file or creates an empty dictionary if missing/invalid."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_data(data):
    """Saves the given inventory data to mining_data.json, ensuring the directory exists."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


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
        "wooden house": {"wood": 8}
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
        self.mining_data = load_data()
        self.recipes = load_recipes()

    #
    # ====== INTERNAL HELPER METHOD ======
    #
    def update_inventory(self, user_id, item, amount=1, save=True):
        """
        Updates a user's inventory by 'amount' of 'item'.
        Prevents negative totals.
        The optional 'save' parameter reduces frequent file writes if set to False.
        """
        user_id = str(user_id)
        if user_id not in self.mining_data:
            self.mining_data[user_id] = {}

        self.mining_data[user_id][item] = self.mining_data[user_id].get(item, 0) + amount
        if self.mining_data[user_id][item] < 0:
            self.mining_data[user_id][item] = 0

        if save:
            save_data(self.mining_data)

    #
    # ====== VIEW FOR MINING BUTTONS ======
    #
    class MineView(discord.ui.View):
        """Simple View for the !mine command: 'Mine Left', 'Mine Right', 'Mine Down'."""
        def __init__(self, user_id, cog):
            super().__init__(timeout=30)
            self.user_id = user_id
            self.cog = cog

        async def interaction_check(self, interaction: discord.Interaction):
            # Only the invoking user can press these
            return interaction.user.id == self.user_id

        @discord.ui.button(label="Mine Left", style=discord.ButtonStyle.primary)
        async def mine_left(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.handle_mine(interaction, "left")

        @discord.ui.button(label="Mine Right", style=discord.ButtonStyle.primary)
        async def mine_right(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.handle_mine(interaction, "right")

        @discord.ui.button(label="Mine Down", style=discord.ButtonStyle.primary)
        async def mine_down(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.handle_mine(interaction, "down")

        async def handle_mine(self, interaction: discord.Interaction, direction: str):
            await interaction.response.defer()

            user_id = str(self.user_id)
            pickaxe_bonus = 2 if self.cog.mining_data.get(user_id, {}).get("pickaxe", 0) > 0 else 1
            # Weighted random resource
            ores = {"stone": 3, "iron": 2, "gold": 1, "diamond": 0.5}
            found = random.choices(list(ores.keys()), weights=ores.values(), k=1)[0]
            amount = random.randint(1, 3) * pickaxe_bonus

            self.cog.update_inventory(user_id, found, amount, save=False)
            save_data(self.cog.mining_data)

            new_content = f"{interaction.user.mention} mined {amount}x **{found}** by going {direction}!"
            await interaction.message.edit(
                content=new_content,
                embed=None,
                view=None
            )
            self.stop()

    #
    # ====== USER COMMANDS ======
    #

    @commands.command()
    async def mine(self, ctx):
        """Start mining with interactive buttons."""
        view = self.MineView(ctx.author.id, self)
        embed = discord.Embed(
            title="Mining",
            description="Choose a direction to mine.\nIf you own a pickaxe, you'll get extra loot!",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed, view=view)

    @commands.command()
    async def chop(self, ctx):
        """Chop wood. If you have an 'axe', you'll collect double."""
        user_id = str(ctx.author.id)
        inventory = self.mining_data.get(user_id, {})
        multiplier = 2 if inventory.get("axe", 0) > 0 else 1
        wood_amount = random.randint(1, 3) * multiplier
        self.update_inventory(ctx.author.id, "wood", wood_amount)
        await ctx.send(f"{ctx.author.mention} chopped wood and collected {wood_amount}x wood!")

    @commands.command()
    async def inventory(self, ctx):
        """Displays your inventory."""
        user_id = str(ctx.author.id)
        inventory = self.mining_data.get(user_id, {})

        if not inventory:
            return await ctx.send("Your inventory is empty. Start mining with `!mine`!")

        items_list = "\n".join([f"**{item}**: {count}" for item, count in inventory.items() if count > 0])
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Inventory",
            description=items_list,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def stats(self, ctx):
        """Shows your total items and number of unique items."""
        user_id = str(ctx.author.id)
        inventory = self.mining_data.get(user_id, {})
        total_items = sum(inventory.values())
        unique_items = len(inventory)

        embed = discord.Embed(title=f"{ctx.author.name}'s Stats", color=discord.Color.purple())
        embed.add_field(name="Total Items Collected", value=str(total_items))
        embed.add_field(name="Unique Items", value=str(unique_items))
        await ctx.send(embed=embed)

    @commands.command()
    async def leaderboard(self, ctx):
        """Shows top miners by total item count."""
        if not self.mining_data:
            return await ctx.send("No data available yet!")

        sorted_users = sorted(self.mining_data.items(), key=lambda x: sum(x[1].values()), reverse=True)
        embed = discord.Embed(title="Top Miners", color=discord.Color.gold())

        for i, (user, inventory) in enumerate(sorted_users[:10], 1):
            total = sum(inventory.values())
            embed.add_field(name=f"{i}. <@{user}>", value=f"{total} items", inline=False)

        await ctx.send(embed=embed)

    #
    # ====== BUILD / CRAFTING COMMANDS ======
    #

    @commands.command()
    async def build(self, ctx, *, structure: str = None):
        """
        Build a structure based on recipes.
        If no structure is specified, calls !buildlist to show all.
        """
        try:
            if structure is None:
                return await ctx.invoke(self.bot.get_command("buildlist"))

            user_id = str(ctx.author.id)
            inventory = self.mining_data.get(user_id, {})

            structure_lower = structure.lower()
            required_items = self.recipes.get(structure_lower)

            if not required_items:
                return await ctx.send("Unknown structure. Use `!buildlist` to see all available structures.")

            # Check resources
            for item, amount_needed in required_items.items():
                if inventory.get(item, 0) < amount_needed:
                    return await ctx.send(f"You don't have enough **{item}** to build **{structure}**.")

            # Subtract cost and give the user the new buildable item
            for item, amount_needed in required_items.items():
                self.update_inventory(ctx.author.id, item, -amount_needed, save=False)
            self.update_inventory(ctx.author.id, structure_lower, 1, save=False)
            save_data(self.mining_data)

            await ctx.send(f"{ctx.author.mention} successfully built a **{structure}**!")
        except Exception as e:
            print(f"[ERROR in build command]: {e}")
            await ctx.send("An unexpected error occurred while trying to build.")

    @commands.command()
    async def buildlist(self, ctx):
        """Shows all craftable structures from recipes.json."""
        try:
            if not self.recipes:
                return await ctx.send("No recipes available at this time.")

            recipe_lines = []
            for structure_name, requirements in self.recipes.items():
                if not isinstance(requirements, dict):
                    continue
                req_str = ", ".join([f"{mat}: {amt}" for mat, amt in requirements.items()])
                recipe_lines.append(f"**{structure_name.title()}**: Requires {req_str}")

            embed = discord.Embed(
                title="Available Structures",
                description="\n".join(recipe_lines),
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"[ERROR in buildlist command]: {e}")
            await ctx.send("An unexpected error occurred while listing buildable structures.")

    @commands.command()
    async def buildable(self, ctx):
        """
        Lists only what the user can currently build based on their inventory.
        """
        user_id = str(ctx.author.id)
        inventory = self.mining_data.get(user_id, {})

        can_build = []
        for structure_name, requirements in self.recipes.items():
            if all(inventory.get(item, 0) >= amt for item, amt in requirements.items()):
                can_build.append(structure_name)

        if not can_build:
            return await ctx.send("You currently don't have enough resources to build anything.")

        embed = discord.Embed(
            title=f"{ctx.author.name}'s Buildable Structures",
            description="\n".join(s.title() for s in can_build),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    #
    # ====== OPTIONAL EXPLORATION / SPECIAL ITEMS ======
    #

    @commands.command()
    async def explore(self, ctx):
        """Discover random events or items."""
        user_id = str(ctx.author.id)
        outcomes = [
            "found 1 gold in an abandoned camp!",
            "stumbled upon a hidden diamond vein and got 1 diamond!",
            "was attacked by monsters and lost 2 stone...",
            "found a secret chest with 3 wood!",
            "got lost and found nothing..."
        ]
        result = random.choice(outcomes)

        if "found 1 gold" in result:
            self.update_inventory(user_id, "gold", 1)
        elif "1 diamond" in result:
            self.update_inventory(user_id, "diamond", 1)
        elif "lost 2 stone" in result:
            self.update_inventory(user_id, "stone", -2)
        elif "3 wood" in result:
            self.update_inventory(user_id, "wood", 3)

        await ctx.send(f"{ctx.author.mention} {result}")

    @commands.command()
    async def use(self, ctx, *, item: str = None):
        """Use a special item from your inventory (e.g., torch, dynamite)."""
        if not item:
            return await ctx.send("Please specify an item to use, e.g. `!use torch`.")

        user_id = str(ctx.author.id)
        item = item.lower()

        if self.mining_data.get(user_id, {}).get(item, 0) < 1:
            return await ctx.send(f"You don't have **{item}** to use.")

        if item == "torch":
            message = "You light a torch and peer into the darkness..."
        elif item == "dynamite":
            message = "You ignite dynamite and blow a new path in the mine!"
        else:
            message = f"You used **{item}**, but nothing special happened."

        self.update_inventory(user_id, item, -1)
        await ctx.send(f"{ctx.author.mention} {message}")

    #
    # ====== ADMIN COMMANDS ======
    #

    @commands.command()
    async def reset_inventory(self, ctx, member: discord.Member):
        """Admin-only: reset a user's inventory."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("You don't have permission to do that.")

        user_id = str(member.id)
        self.mining_data[user_id] = {}
        save_data(self.mining_data)
        await ctx.send(f"{member.name}'s inventory has been reset.")

    @commands.command()
    async def give(self, ctx, member: discord.Member, item: str, amount: int):
        """Admin-only: give resources to a user."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("You don't have permission to do that.")

        item = item.lower()
        self.update_inventory(member.id, item, amount)
        await ctx.send(f"Gave {amount}x **{item}** to {member.name}.")


#
# ===== SETUP FUNCTION =====
#

async def setup(bot):
    await bot.add_cog(MiningCog(bot))