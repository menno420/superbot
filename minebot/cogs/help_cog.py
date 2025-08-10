# help_cog.py (enhanced owner-only utils command)
import discord
from discord.ext import commands
from helpers.embed_helper import create_embed, error_embed
from helpers.button_helper import create_button_view
import os, inspect
import importlib
from config import Config

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Main help command remains unchanged, except for owner check on utils button
    @commands.hybrid_command(name="help", description="Shows help menu.")
    async def help(self, ctx):
        embed = create_embed(
            title="⛏️ MineBot Help",
            description="Select a category to view available commands:",
            color=discord.Color.blue()
        )

        buttons = []

        for cog_name, cog in self.bot.cogs.items():
            async def cog_callback(interaction, cog=cog, cog_name=cog_name):
                cmd_list = [f"**{cmd.name}** - {cmd.help or 'No description.'}" for cmd in cog.get_commands()]
                cmd_text = "\n".join(cmd_list) if cmd_list else "No commands available."
                embed = create_embed(
                    title=f"📜 {cog_name} Commands",
                    description=cmd_text,
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

            buttons.append(
                (cog_name, discord.ButtonStyle.secondary, cog_callback)
            )

        # Owner-only Utils Button
        if ctx.author.id == Config.BOT_OWNER_ID:
            async def utils_callback(interaction):
                utils_dir = Config.UTILS_DIR
                util_files = [f[:-3] for f in os.listdir(utils_dir) if f.endswith(".py") and f != "__init__.py"]

                buttons = []
                for util in util_files:
                    async def util_callback(inner_interaction, util=util):
                        embed = await self.get_util_functions_embed(util)
                        await inner_interaction.response.send_message(embed=embed, ephemeral=True)

                    buttons.append((util, discord.ButtonStyle.primary, util_callback))

                util_embed = create_embed(
                    title="🔧 Utils Modules",
                    description="Select a utility module to view its functions:",
                    color=discord.Color.orange()
                )
                util_view = create_button_view(buttons)
                await interaction.response.send_message(embed=util_embed, view=util_view, ephemeral=True)

            buttons.append(("Utils (Owner Only)", discord.ButtonStyle.danger, utils_callback))

        view = create_button_view(buttons)
        await ctx.send(embed=embed, view=view)

    # Helper method to get functions and their descriptions dynamically
    async def get_util_functions_embed(self, util_name):
        try:
            module_path = f"utils.{util_name}"
            module = importlib.import_module(module_path)
            functions = inspect.getmembers(module, inspect.isfunction)

            if not functions:
                return error_embed(f"No functions found in `{util_name}`.")

            description = ""
            for name, func in functions:
                doc = inspect.getdoc(func) or "No description available."
                description += f"**`{name}`**: {doc}\n"

            embed = create_embed(
                title=f"📖 Functions in `{util_name}`",
                description=description,
                color=discord.Color.teal()
            )
            return embed
        except Exception as e:
            return error_embed(f"Error loading `{util_name}`: {e}")

async def setup(bot):
    await bot.add_cog(HelpCog(bot))