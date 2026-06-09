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
# from ..services import activity_service  # TODO: Extend later

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
        # Access core services (adjust based on your exact setup)
        self.session_manager = getattr(self.bot, "session_manager", None)
        self.event_bus = getattr(self.bot, "event_bus", None)
        logger.info("CommunitySpotlight cog loaded")

    @commands.command(name="spotlight", aliases=["hub", "activity"])
    @commands.has_permissions(manage_guild=True)
    async def spotlight(self, ctx: commands.Context):
        """Open the Community Spotlight dashboard (persistent)."""
        embed = self._create_main_dashboard_embed(ctx.guild)
        view = SpotlightView(self)

        await ctx.send(embed=embed, view=view)

    def _create_main_dashboard_embed(self, guild: discord.Guild) -> discord.Embed:
        """Create the main dashboard embed."""
        embed = discord.Embed(
            title="🌟 Community Spotlight",
            description="Live server vibes & highlights",
            color=discord.Color.purple(),
        )
        embed.add_field(
            name="Most Active Channel", value="#general • 42 msgs today", inline=True
        )
        embed.add_field(name="Top Member", value="@User • 15 msgs", inline=True)
        embed.add_field(
            name="Meme of the Week", value="😂 [View Meme]", inline=False
        )
        embed.set_footer(text="Use buttons below • Fully customizable in /settings")
        return embed

    @tasks.loop(minutes=30)
    async def update_loop(self):
        """Background updates for live data."""
        # TODO: Integrate with real activity tracking service
        pass


class SpotlightView(discord.ui.View):
    """Persistent view for the spotlight dashboard."""

    def __init__(self, cog: CommunitySpotlight):
        super().__init__(timeout=None)  # Persistent view
        self.cog = cog

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.gray, emoji="🔄")
    async def refresh(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = self.cog._create_main_dashboard_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Suggest Activity", style=discord.ButtonStyle.green, emoji="🎲"
    )
    async def suggest_activity(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "How about a quick game night or movie watch party?", ephemeral=True
        )


async def setup(bot: commands.Bot):
    """Setup the cog."""
    await bot.add_cog(CommunitySpotlight(bot))
