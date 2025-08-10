import discord
from discord.ext import commands
import json
import os
import difflib

# Define file paths
DATA_DIR = "/home/menno/minebot/data/"
ITEM_ALIASES_PATH = os.path.join(DATA_DIR, "item_aliases.json")
ITEM_STATS_PATH = os.path.join(DATA_DIR, "item_stats.json")

def load_json(file_path):
    """Loads a JSON file safely."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"❌ Failed to load {file_path}")
        return {}

class ItemsCog(commands.Cog):
    """Cog that provides item name parsing, metadata lookup, and categorization."""

    def __init__(self, bot):
        self.bot = bot
        self.item_aliases = load_json(ITEM_ALIASES_PATH)  # Loads item name variations
        self.item_stats = load_json(ITEM_STATS_PATH)  # Loads item stats (weight, durability, rarity)

    def normalize_item_name(self, user_input):
        """
        Converts user input into a canonical item name and category by comparing against all synonyms.
        Returns (canonical_item, category) if found, else (None, None).
        """
        normalized_input = user_input.strip().lower().replace("_", " ")

        best_match = None
        best_category = None
        best_ratio = 0.0

        for category, items_dict in self.item_aliases.items():
            for canonical_item, synonyms in items_dict.items():
                for synonym in synonyms:
                    norm_synonym = synonym.strip().lower().replace("_", " ")
                    ratio = difflib.SequenceMatcher(None, normalized_input, norm_synonym).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_match = canonical_item
                        best_category = category

        # Only accept matches with a high enough confidence score
        if best_ratio >= 0.7:
            return best_match, best_category

        return None, None

    def get_item_stats(self, item_name):
        """
        Retrieves an item's stats (weight, durability, rarity).
        Returns a dictionary of stats or None if item is not found.
        """
        return self.item_stats.get(item_name, None)

    def get_item_category(self, item_name):
        """
        Returns the category of an item based on `item_aliases.json`.
        """
        for category, items_dict in self.item_aliases.items():
            if item_name in items_dict:
                return category
        return None

    @commands.command()
    async def iteminfo(self, ctx, *, item: str):
        """Shows detailed stats of an item, including weight, durability, and rarity."""
        canonical_item, category = self.normalize_item_name(item)

        if not canonical_item:
            return await ctx.send(f"❌ Item `{item}` not found. Check your spelling or try another name!")

        item_stats = self.get_item_stats(canonical_item)

        if not item_stats:
            return await ctx.send(f"❌ No stats available for `{canonical_item}`.")

        embed = discord.Embed(title=f"📜 Item Info: {canonical_item.title()}", color=discord.Color.blue())
        embed.add_field(name="Category", value=category.title() if category else "Unknown", inline=True)
        embed.add_field(name="Weight", value=item_stats.get("weight", "Unknown"), inline=True)
        embed.add_field(name="Durability", value=item_stats.get("durability", "None"), inline=True)
        embed.add_field(name="Rarity", value=item_stats.get("rarity", "Unknown"), inline=True)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ItemsCog(bot))