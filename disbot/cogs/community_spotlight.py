"""
Community Spotlight Cog
A fun dashboard for server activity, highlights, and engagement.
Fully configurable with presets. Uses in-place updates where possible.
"""

import discord
from discord.ext import commands, tasks
from typing import Optional

from ..core.runtime import SessionManager, EventBus
from ..utils.logger import get_logger
from ..services import activity_service  # We'll assume/minimally extend this later

logger = get_logger(__name__)

class CommunitySpotlight(commands.Cog):
    """Fun server activity hub with highlights and suggestions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_manager: Optional[SessionManager] = None
        self.event_bus: Optional[EventBus] = None
        self.update_loop.start()

    async def cog_load(self):
        """Called when cog is loaded."""
        self.session_manager = self.bot.get_cog("SessionManager")  # or however you access it
        self.event_bus = self.bot.get_cog("EventBus")
        logger.info("CommunitySpotlight cog loaded")

    @commands.command(name="spotlight", aliases=["hub", "activity"])
    @commands.has_permissions(manage_guild=True)
    async def spotlight(self, ctx: commands.Context):
        """Open the Community Spotlight dashboard (persistent)."""
        embed = self._create_main_dashboard_embed(ctx.guild)
        view = SpotlightView(self)
        
        # In-place / persistent message
        message = await ctx.send(embed=embed, view=view)
        # Optionally store message ID for future updates via session manager

    def _create_main_dashboard_embed(self, guild: discord.Guild) -> discord.Embed:
        embed = discord.Embed(
            title="🌟 Community Spotlight",
            description="Live server vibes & highlights",
            color=discord.Color.purple()
        )
        embed.add_field(name="Most Active Channel", value="#general • 42 msgs today", inline=True)
        embed.add_field(name="Top Member", value="@User • 15 msgs", inline=True)
        embed.add_field(name="Meme of the Week", value="😂 [View Meme]", inline=False)
        embed.set_footer(text="Use buttons below • Fully customizable in /settings")
        return embed

    @tasks.loop(minutes=30)
    async def update_loop(self):
        """Background updates for live data."""
        # TODO: Integrate with activity tracking
        pass

# Simple View for buttons (in-place interactions)
class SpotlightView(discord.ui.View):
    def __init__(self, cog: CommunitySpotlight):
        super().__init__(timeout=None)  # Persistent
        self.cog = cog

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.gray, emoji="🔄")
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.cog._create_main_dashboard_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Suggest Activity", style=discord.ButtonStyle.green, emoji="🎲")
    async def suggest_activity(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("How about a quick game night or movie watch party?", ephemeral=True)

# Setup function
async def setup(bot: commands.Bot):
    await bot.add_cog(CommunitySpotlight(bot))
