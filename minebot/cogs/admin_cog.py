import discord
from discord.ext import commands
from helpers.embed_helper import success_embed, error_embed
from utils.admin import (
    restart_bot,
    reload_all_cogs,
    reload_json_files,
    reload_modules,
    load_cog,
    unload_cog,
    reload_cog
)
from config import Config

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="restart_bot", help="Restarts the bot process (Owner Only)")
    @commands.is_owner()
    async def restart(self, ctx):
        await ctx.send(embed=success_embed("🔁 Restarting bot now..."))
        await restart_bot(self.bot)

    @commands.command(name="reload_cogs", help="Reload all default cogs")
    @commands.is_owner()
    async def reload_cogs(self, ctx):
        await reload_all_cogs(self.bot, Config.INITIAL_COGS)
        await ctx.send(embed=success_embed("✅ All default cogs have been reloaded."))

    @commands.command(name="reload_json", help="Reload static JSON files")
    @commands.is_owner()
    async def reload_json(self, ctx):
        data = reload_json_files()
        if data:
            await ctx.send(embed=success_embed("📁 JSON files have been reloaded."))
        else:
            await ctx.send(embed=error_embed("❌ Failed to reload one or more JSON files."))

    @commands.command(name="reload_modules", help="Reload all helpers and utils")
    @commands.is_owner()
    async def reload_modules_cmd(self, ctx):
        modules = reload_modules()
        if modules:
            modules_list = '\n'.join(f"🔄 {m}" for m in modules)
            await ctx.send(embed=success_embed(f"✅ Reloaded modules:\n{modules_list}"))
        else:
            await ctx.send(embed=error_embed("❌ No modules reloaded."))

    @commands.command(name="cog", help="Dynamically load/reload/unload a cog by name")
    @commands.is_owner()
    async def manage_cog_command(self, ctx, action: str, cogname: str):  # ✅ FIXED name
        cog_path = f"cogs.{cogname.lower()}_cog"
        try:
            if action.lower() == "load":
                await load_cog(self.bot, cog_path)
                await ctx.send(embed=success_embed(f"✅ Loaded `{cogname}_cog` successfully."))
            elif action.lower() == "reload":
                await reload_cog(self.bot, cog_path)
                await ctx.send(embed=success_embed(f"🔄 Reloaded `{cogname}_cog` successfully."))
            elif action.lower() == "unload":
                await unload_cog(self.bot, cog_path)
                await ctx.send(embed=success_embed(f"🗑️ Unloaded `{cogname}_cog` successfully."))
            else:
                await ctx.send(embed=error_embed("❌ Action must be `load`, `reload`, or `unload`."))
        except Exception as e:
            await ctx.send(embed=error_embed(f"❌ Error managing cog `{cogname}_cog`: {e}"))

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
