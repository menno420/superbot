import discord
from discord.ext import commands
from helpers.embed_helper import create_embed, success_embed, error_embed
from helpers.button_helper import create_button_view
from utils.data_manager import DatabaseManager

# We'll use discord.ui.Modal for collecting input.
class VersionModal(discord.ui.Modal, title="Update Bot Version"):
    version = discord.ui.TextInput(label="New Version", placeholder="e.g. 1.0.6", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        current_info = await DatabaseManager.get_bot_info()
        changelog = current_info.get("changelog") or ""
        await DatabaseManager.update_bot_info(self.version.value, changelog)
        await interaction.response.send_message(success_embed(f"Bot version updated to **{self.version.value}**."), ephemeral=True)

class ChangelogModal(discord.ui.Modal, title="Update Changelog"):
    changelog = discord.ui.TextInput(label="New Changelog", style=discord.TextStyle.paragraph, placeholder="Enter the new changelog here...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        current_info = await DatabaseManager.get_bot_info()
        version = current_info.get("version") or "N/A"
        await DatabaseManager.update_bot_info(version, self.changelog.value)
        await interaction.response.send_message(success_embed("Changelog updated successfully."), ephemeral=True)

class BotStatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.default_version = "1.0.5"

    @commands.hybrid_command(name="ping", description="Checks bot latency.")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000, 2)
        embed = create_embed(
            title="🏓 Pong!",
            description=f"Latency: **{latency} ms**",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="version", description="Shows current bot version and changelog.")
    async def version_command(self, ctx):
        bot_info = await DatabaseManager.get_bot_info()
        version = bot_info.get("version") or self.default_version
        changelog = bot_info.get("changelog") or "No changelog available yet."
        embed = create_embed(
            title="🤖 Bot Version",
            description=f"Current version: **{version}**\n\nChangelog:\n{changelog}",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="updatebotinfo", description="Update the bot version or changelog. (Owner only)")
    @commands.is_owner()
    async def updatebotinfo(self, ctx):
        # This command will send a message with two buttons.
        async def update_version_callback(interaction: discord.Interaction):
            modal = VersionModal()
            await interaction.response.send_modal(modal)

        async def update_changelog_callback(interaction: discord.Interaction):
            modal = ChangelogModal()
            await interaction.response.send_modal(modal)

        buttons = [
            ("Update Version", discord.ButtonStyle.primary, update_version_callback),
            ("Update Changelog", discord.ButtonStyle.primary, update_changelog_callback)
        ]
        view = create_button_view(buttons)
        embed = create_embed(
            title="Update Bot Info",
            description="Choose which information to update:",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(BotStatsCog(bot))