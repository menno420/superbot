import discord
from discord.ext import commands
import json
from config import Config
from utils.data_manager import DatabaseManager
from helpers.embed_helper import success_embed, error_embed

class MigrationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def migrate_item_stats(self):
        try:
            with open(Config.ITEM_STATS_FILE, "r", encoding="utf-8") as f:
                items_data = json.load(f)
        except Exception as e:
            return False, f"Failed to load item stats: {e}"

        insert_query = """
            INSERT OR REPLACE INTO items
            (item_id, display_name, category, rarity, value, weight, description, other_stats)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        for item_id, data in items_data.items():
            display_name = data.get("display_name", item_id)
            category = data.get("category", "")
            rarity = data.get("rarity", "")
            value = data.get("value", 0)
            weight = data.get("weight", 0)
            description = data.get("description", "")
            other_stats = {k: v for k, v in data.items() if k not in ["display_name", "category", "rarity", "value", "weight", "description"]}
            other_stats_json = json.dumps(other_stats) if other_stats else None
            await DatabaseManager.execute_query(insert_query, (item_id, display_name, category, rarity, value, weight, description, other_stats_json))
        return True, f"Migrated {len(items_data)} items."

    async def migrate_item_aliases(self):
        try:
            with open(Config.ITEM_ALIASES_FILE, "r", encoding="utf-8") as f:
                aliases_data = json.load(f)
        except Exception as e:
            return False, f"Failed to load aliases: {e}"

        insert_query = "INSERT OR REPLACE INTO item_aliases (alias, item_id) VALUES (?, ?)"
        total = 0
        for category, items in aliases_data.items():
            for canonical, variants in items.items():
                await DatabaseManager.execute_query(insert_query, (canonical.lower(), canonical))
                for variant in variants:
                    await DatabaseManager.execute_query(insert_query, (variant.lower(), canonical))
                    total += 1
        return True, f"Migrated {total} aliases."

    @commands.hybrid_command(name="migrate_items", description="Migrate item stats to SQLite.")
    @commands.is_owner()
    async def migrate_items(self, ctx):
        await ctx.defer()
        await DatabaseManager.initialize()
        success, message = await self.migrate_item_stats()
        if success:
            await ctx.send(embed=success_embed(message))
        else:
            await ctx.send(embed=error_embed(message))

    @commands.hybrid_command(name="migrate_aliases", description="Migrate item aliases to SQLite.")
    @commands.is_owner()
    async def migrate_aliases(self, ctx):
        await ctx.defer()
        await DatabaseManager.initialize()
        success, message = await self.migrate_item_aliases()
        if success:
            await ctx.send(embed=success_embed(message))
        else:
            await ctx.send(embed=error_embed(message))

    @commands.hybrid_command(name="runmigration", description="Run full data migration to SQLite.")
    @commands.is_owner()
    async def runmigration(self, ctx):
        await ctx.defer()
        await DatabaseManager.initialize()
        results = []

        for func in [self.migrate_item_stats, self.migrate_item_aliases]:
            success, msg = await func()
            results.append((success, msg))

        if all(r[0] for r in results):
            desc = "\n".join(f"• {msg}" for _, msg in results)
            await ctx.send(embed=success_embed(f"All migrations completed:\n{desc}"))
        else:
            failures = "\n".join(f"❌ {msg}" for s, msg in results if not s)
            await ctx.send(embed=error_embed(f"Migrations failed:\n{failures}"))

async def setup(bot):
    await bot.add_cog(MigrationCog(bot))