import discord
from discord.ext import commands, tasks

from ..utils.logger import get_logger
from ..views.base import BaseView

logger = get_logger(__name__)


class CommunitySpotlight(commands.Cog):
    """Fun server activity hub with highlights and suggestions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.update_loop.start()
        logger.info("CommunitySpotlight cog loaded")

    async def cog_unload(self) -> None:
        self.update_loop.cancel()

    @commands.command(name="spotlight", aliases=["hub", "activity"])
    @commands.has_permissions(manage_guild=True)
    async def spotlight(self, ctx: commands.Context) -> None:
        """Open the Community Spotlight dashboard."""
        embed = _create_dashboard_embed()
        view = SpotlightView(ctx.author, public=True)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    @tasks.loop(minutes=30)
    async def update_loop(self) -> None:
        # TODO: Integrate with real activity tracking service
        pass


class SpotlightView(BaseView):
    """Interactive panel for the Community Spotlight dashboard."""

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.gray, emoji="🔄")
    async def refresh(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        embed = _create_dashboard_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Suggest Activity",
        style=discord.ButtonStyle.green,
        emoji="🎲",
    )
    async def suggest_activity(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            "How about a quick game night or movie watch party?",
            ephemeral=True,
        )


def _create_dashboard_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Community Spotlight",
        description="Live server vibes & highlights",
        color=discord.Color.purple(),
    )
    embed.add_field(
        name="Most Active Channel",
        value="#general • 42 msgs today",
        inline=True,
    )
    embed.add_field(name="Top Member", value="@User • 15 msgs", inline=True)
    embed.add_field(name="Meme of the Week", value="😂 [View Meme]", inline=False)
    embed.set_footer(text="Use buttons below • Fully customizable in /settings")
    return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommunitySpotlight(bot))
