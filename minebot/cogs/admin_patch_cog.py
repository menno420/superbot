import discord
from discord.ext import commands
import aiosqlite
from config import Config
from helpers.embed_helper import success_embed, error_embed

class AdminPatchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="patch_items_table", description="Admin-only: fix equipable item categories in DB")
    @commands.is_owner()
    async def patch_items_table(self, ctx: commands.Context):
        patch_sql = """
        UPDATE items SET category = 'weapon'
        WHERE item_id LIKE '%sword%' AND (category IS NULL OR category = '');
        UPDATE items SET category = 'tool'
        WHERE item_id LIKE '%pickaxe%' AND (category IS NULL OR category = '');
        UPDATE items SET category = 'tool'
        WHERE item_id LIKE '%axe%' AND (category IS NULL OR category = '');
        UPDATE items SET category = 'armor'
        WHERE item_id LIKE '%helmet%' AND (category IS NULL OR category = '');
        UPDATE items SET category = 'armor'
        WHERE item_id LIKE '%chestplate%' AND (category IS NULL OR category = '');
        UPDATE items SET category = 'armor'
        WHERE item_id LIKE '%boots%' AND (category IS NULL OR category = '');
        """
        try:
            async with aiosqlite.connect(Config.DB_FILE) as db:
                await db.executescript(patch_sql)
                await db.commit()
            await ctx.send(embed=success_embed("✅ Patch applied: item categories updated."))
        except Exception as e:
            await ctx.send(embed=error_embed(f"❌ Failed to patch: {e}"))

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminPatchCog(bot))
