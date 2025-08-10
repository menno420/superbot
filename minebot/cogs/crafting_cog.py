import discord
from discord.ext import commands
import json
import asyncio
import difflib
from config import Config
from utils.data_manager import DatabaseManager  # New data manager
from helpers.crafting_ui_helper import CraftOptionsView

# Optionally, import caching helpers from data_manager if needed

# ---------------------------
# ALIASES & FUZZY MATCH HELPERS
# ---------------------------

ALIASES_FILE = Config.ITEM_ALIASES_FILE  # Path to aliases JSON

def load_aliases():
    try:
        with open(ALIASES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading aliases: {e}")
        return {}

ITEM_ALIASES = load_aliases()

def normalize_item_name(user_input: str):
    normalized_input = user_input.strip().lower().replace("_", " ")
    best_match = None
    best_category = None
    best_ratio = 0.0

    for category, items_dict in ITEM_ALIASES.items():
        for canonical_item, synonyms in items_dict.items():
            for synonym in synonyms:
                norm_synonym = synonym.strip().lower().replace("_", " ")
                ratio = difflib.SequenceMatcher(None, normalized_input, norm_synonym).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = canonical_item
                    best_category = category

    if best_ratio >= 0.7:
        return best_match, best_category
    return None, None

def normalize_string(s: str) -> str:
    return " ".join(sorted(s.lower().split()))

# ---------------------------
# PAGINATION & CATEGORY UI VIEWS (unchanged)
# ---------------------------
# ... (Assume these views remain the same) ...

# ---------------------------
# CraftingCog
# ---------------------------
class CraftingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.recipes = self.load_recipes()  # Recipes remain loaded from file for now
        self.crafting_xp = {}  # Track crafting XP by user ID
        self.recipes_by_category = self.group_recipes_by_category(self.recipes)

    def load_recipes(self):
        try:
            with open(Config.RECIPES_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading recipes: {e}")
            return {}

    # --- Inventory Helpers using DatabaseManager ---
    async def get_inventory(self, user_id: str) -> dict:
        """Get user inventory from the database."""
        data = await DatabaseManager.get_inventory(user_id)
        return data  # Inventory as a dict: { item_id: quantity, ... }

    async def update_inventory(self, user_id: str, item_id: str, delta: int):
        """Update inventory for a specific item."""
        return await DatabaseManager.update_inventory(user_id, item_id, delta)

    async def get_craftable_items(self, user_id: str) -> list:
        inventory = await self.get_inventory(user_id)
        craftable = []
        for item_name, recipe in self.recipes.items():
            if all(inventory.get(mat, 0) >= req for mat, req in recipe.items()):
                craftable.append(item_name)
        return craftable

    # --- Fuzzy Matching Helpers ---
    def get_closest_recipe(self, item: str) -> str:
        canonical_item, _ = normalize_item_name(item)
        if canonical_item and canonical_item in self.recipes:
            return canonical_item

        if item in self.recipes:
            return item

        norm_input = normalize_string(item)
        best_match = None
        best_ratio = 0.0
        for recipe in self.recipes:
            norm_recipe = normalize_string(recipe)
            ratio = difflib.SequenceMatcher(None, norm_input, norm_recipe).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = recipe
        if best_ratio >= 0.7:
            return best_match

        return None

    # --- Recipe Categorization Helpers (unchanged) ---
    def categorize_recipe(self, item_name: str) -> str:
        name_lower = item_name.lower()
        if any(kw in name_lower for kw in ["sword", "dagger", "bow", "gun", "mace", "staff"]):
            return "Weapons"
        elif any(kw in name_lower for kw in ["helmet", "armour", "chestplate", "boots", "leggings", "shield"]):
            return "Armour"
        elif any(kw in name_lower for kw in ["pickaxe", "shovel", "hoe", "axe", "hammer", "tool"]):
            return "Tools"
        else:
            return "Items"

    def group_recipes_by_category(self, recipes: dict) -> dict:
        grouped = {}
        for item in recipes.keys():
            category = self.categorize_recipe(item)
            grouped.setdefault(category, {})[item] = recipes[item]
        return grouped

    def get_recipe_categories(self) -> list:
        categories = set(self.categorize_recipe(recipe) for recipe in self.recipes)
        return sorted(list(categories))

    def get_recipes_by_category(self, category: str) -> list:
        return [recipe for recipe in self.recipes if self.categorize_recipe(recipe) == category]

    def build_paginated_embeds(self, recipes_grouped: dict) -> list:
        # This function remains largely unchanged
        embeds = []
        for category, recipes in recipes_grouped.items():
            lines = []
            for item, ingredients in recipes.items():
                ing_text = ", ".join(f"{ing} x{amt}" for ing, amt in ingredients.items())
                lines.append(f"**{item}**: {ing_text}")
            description = "\n".join(lines) if lines else "No recipes available."
            embed = discord.Embed(title=f"{category} Recipes", description=description, color=discord.Color.blue())
            embeds.append(embed)
        return embeds

    # --- Auto-crafting Submaterials (refactored to use DatabaseManager) ---
    async def auto_craft_material(self, user_id: str, material: str, needed_amount: int) -> bool:
        if material not in self.recipes:
            return False

        inventory = await self.get_inventory(user_id)
        have = inventory.get(material, 0)
        shortfall = needed_amount - have
        if shortfall <= 0:
            return True

        sub_recipe = self.recipes[material]
        for sub_mat, sub_amt in sub_recipe.items():
            required_sub = sub_amt * shortfall
            have_sub = inventory.get(sub_mat, 0)
            if have_sub < required_sub:
                success = await self.auto_craft_material(user_id, sub_mat, required_sub)
                if not success:
                    return False
            inventory = await self.get_inventory(user_id)
            if inventory.get(sub_mat, 0) < required_sub:
                return False

        for sub_mat, sub_amt in sub_recipe.items():
            await self.update_inventory(user_id, sub_mat, -sub_amt * shortfall)
        await self.update_inventory(user_id, material, shortfall)
        return True

    # --- Craft Command ---
    @commands.hybrid_command(name="craft", with_app_command=True)
    async def craft(self, ctx: commands.Context, *, args: str = None):
        user_id = str(ctx.author.id)
        # Ensure the user exists in the database.
        await DatabaseManager.add_user_if_not_exists(user_id, ctx.author.display_name)

        if args is None:
            embed = discord.Embed(
                title="Craft",
                description="Choose one of the options below:",
                color=discord.Color.blue()
            )
            # Assume CraftOptionsView remains unchanged
            view = CraftOptionsView(self, user_id)
            await ctx.send(embed=embed, view=view)
            return

        tokens = args.split()
        try:
            amount = int(tokens[-1])
            item_name = " ".join(tokens[:-1]).strip() or tokens[-1]
        except ValueError:
            amount = 1
            item_name = args

        recipe_key = self.get_closest_recipe(item_name)
        if not recipe_key:
            await ctx.send(embed=discord.Embed(title="Error", description="Recipe not found.", color=discord.Color.red()))
            return

        recipe = self.recipes.get(recipe_key)
        crafted_count = 0
        total_xp = 0

        for i in range(amount):
            inventory = await self.get_inventory(user_id)
            for mat, req_amt in recipe.items():
                if inventory.get(mat, 0) < req_amt:
                    success = await self.auto_craft_material(user_id, mat, req_amt)
                    if not success:
                        break
                inventory = await self.get_inventory(user_id)
            missing = {m: recipe[m] - inventory.get(m, 0) for m in recipe if inventory.get(m, 0) < recipe[m]}
            if missing:
                missing_text = "\n".join(f"- {m}: missing {qty}" for m, qty in missing.items())
                await ctx.send(embed=discord.Embed(title="Error", description=f"Cannot craft **{recipe_key}**:\n{missing_text}", color=discord.Color.red()))
                break

            for mat, req_amt in recipe.items():
                await self.update_inventory(user_id, mat, -req_amt)
            await self.update_inventory(user_id, recipe_key, 1)
            xp_gained = sum(recipe.values())
            self.crafting_xp[user_id] = self.crafting_xp.get(user_id, 0) + xp_gained
            crafted_count += 1
            total_xp += xp_gained

        if crafted_count == 0:
            return
        elif crafted_count < amount:
            await ctx.send(embed=discord.Embed(title="Partial Success", description=f"Crafted {crafted_count}x **{recipe_key}**. (+{total_xp} XP)", color=discord.Color.orange()))
        else:
            await ctx.send(embed=discord.Embed(title="Success", description=f"Crafted {crafted_count}x **{recipe_key}**! (+{total_xp} XP)", color=discord.Color.green()))

    # Additional commands like recipe_detail, recipes_using, missing, reload_recipes, and crafting_top remain largely similar,
    # except that any inventory interactions now use DatabaseManager-based functions.

    @commands.hybrid_command(name="recipe", with_app_command=True)
    async def recipe_detail(self, ctx: commands.Context, *, item: str):
        recipe_key = self.get_closest_recipe(item)
        if not recipe_key:
            await ctx.send(embed=discord.Embed(title="Error", description="That item is not craftable!", color=discord.Color.red()))
            return
        recipe = self.recipes[recipe_key]
        lines = [f"{mat}: {amt}" for mat, amt in recipe.items()]
        description = "\n".join(lines)
        await ctx.send(embed=discord.Embed(title=f"Recipe for {recipe_key}", description=description, color=discord.Color.blue()))

    @commands.hybrid_command(name="recipes_using", with_app_command=True)
    async def recipes_using(self, ctx: commands.Context, *, material: str):
        used_in = [item for item, reqs in self.recipes.items() if material in reqs]
        if not used_in:
            await ctx.send(embed=discord.Embed(title="Error", description=f"No items use **{material}** as an ingredient.", color=discord.Color.red()))
        else:
            used_list = "\n".join(f"- {u}" for u in used_in)
            await ctx.send(embed=discord.Embed(title=f"Items using {material}", description=used_list, color=discord.Color.blue()))

    @commands.hybrid_command(name="missing", with_app_command=True)
    async def missing(self, ctx: commands.Context, *, item: str):
        user_id = str(ctx.author.id)
        recipe_key = self.get_closest_recipe(item)
        if not recipe_key:
            await ctx.send(embed=discord.Embed(title="Error", description="That item is not craftable!", color=discord.Color.red()))
            return
        inventory = await self.get_inventory(user_id)
        recipe = self.recipes[recipe_key]
        missing_mats = {m: recipe[m] - inventory.get(m, 0) for m in recipe if inventory.get(m, 0) < recipe[m]}
        if not missing_mats:
            await ctx.send(embed=discord.Embed(title="Info", description=f"You have all the materials for **{recipe_key}**!", color=discord.Color.green()))
        else:
            missing_text = "\n".join(f"- {m}: {a}" for m, a in missing_mats.items())
            await ctx.send(embed=discord.Embed(title="Missing Materials", description=f"Missing for **{recipe_key}**:\n{missing_text}", color=discord.Color.red()))

    @commands.hybrid_command(name="reload_recipes", with_app_command=True)
    async def reload_recipes(self, ctx: commands.Context):
        self.recipes = self.load_recipes()
        self.recipes_by_category = self.group_recipes_by_category(self.recipes)
        await ctx.send(embed=discord.Embed(title="Success", description="Recipes reloaded!", color=discord.Color.green()))

    @commands.hybrid_command(name="crafting_top", with_app_command=True)
    async def crafting_top(self, ctx: commands.Context):
        if not self.crafting_xp:
            await ctx.send("No one has crafted anything yet!")
            return
        top_crafters = sorted(self.crafting_xp.items(), key=lambda x: x[1], reverse=True)[:10]
        lines = []
        for uid, xp in top_crafters:
            member = ctx.guild.get_member(int(uid))
            if member:
                lines.append(f"{member.display_name}: {xp} XP")
            else:
                lines.append(f"Unknown ({uid}): {xp} XP")
        leaderboard = "\n".join(lines)
        await ctx.send(embed=discord.Embed(title="Top Crafters", description=leaderboard, color=discord.Color.gold()))

    @commands.hybrid_command(name="recipes", with_app_command=True)
    async def list_recipes(self, ctx: commands.Context):
        if not self.recipes:
            await ctx.send(embed=discord.Embed(title="Error", description="No recipes found!", color=discord.Color.red()))
            return
        view = RecipeCategoryView(self)  # Assuming this view uses get_recipe_categories() etc.
        await ctx.send("Select a category to view recipes:", view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(CraftingCog(bot))