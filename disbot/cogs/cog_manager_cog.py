import discord
from discord.ext import commands
import os
import logging

logger = logging.getLogger("bot")

COGS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_all_cog_modules() -> list[tuple[str, str]]:
    """Returns (module_path, display_name) for every *_cog.py file in the cogs directory."""
    result = []
    for fname in sorted(os.listdir(COGS_DIR)):
        if fname.endswith("_cog.py") and not fname.startswith("__"):
            module_name = fname[:-3]
            display = module_name.replace("_cog", "").replace("_", " ").title()
            result.append((f"cogs.{module_name}", display))
    return result


def build_status_embed(bot: commands.Bot) -> discord.Embed:
    loaded = set(bot.extensions.keys())
    all_cogs = get_all_cog_modules()
    lines = []
    for module_path, display_name in all_cogs:
        icon = "✅" if module_path in loaded else "❌"
        lines.append(f"{icon} **{display_name}**")
    embed = discord.Embed(
        title="🔧 Cog Manager",
        description="\n".join(lines) or "No cogs found.",
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Select a cog, then press Load / Unload / Reload.")
    return embed


class CogSelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot):
        loaded = set(bot.extensions.keys())
        all_cogs = get_all_cog_modules()
        options = [
            discord.SelectOption(
                label=f"{'✅' if mp in loaded else '❌'} {dn}",
                value=mp,
                description="Loaded" if mp in loaded else "Not loaded",
            )
            for mp, dn in all_cogs
        ]
        super().__init__(
            placeholder="Select a cog…",
            min_values=1,
            max_values=1,
            options=options[:25],
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_cog = self.values[0]
        await interaction.response.defer()


class CogManagerView(discord.ui.View):
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        super().__init__(timeout=180)
        self.bot = bot
        self.ctx = ctx
        self.selected_cog: str | None = None
        self._select = CogSelect(bot)
        self.add_item(self._select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This menu is not for you.", ephemeral=True)
            return False
        return True

    async def _refresh(self, interaction: discord.Interaction):
        self.remove_item(self._select)
        self._select = CogSelect(self.bot)
        self.add_item(self._select)
        await interaction.message.edit(embed=build_status_embed(self.bot), view=self)

    @discord.ui.button(label="Load", style=discord.ButtonStyle.green, row=1)
    async def load_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if not self.selected_cog:
            await interaction.followup.send("Select a cog first.", ephemeral=True)
            return
        try:
            await self.bot.load_extension(self.selected_cog)
            logger.info(f"Loaded {self.selected_cog} by {interaction.user}")
            await interaction.followup.send(f"✅ Loaded `{self.selected_cog}`.", ephemeral=True)
        except commands.ExtensionAlreadyLoaded:
            await interaction.followup.send("⚠️ Already loaded.", ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to load {self.selected_cog}: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Failed to load: `{e}`", ephemeral=True)
        await self._refresh(interaction)

    @discord.ui.button(label="Unload", style=discord.ButtonStyle.red, row=1)
    async def unload_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if not self.selected_cog:
            await interaction.followup.send("Select a cog first.", ephemeral=True)
            return
        if "cog_manager_cog" in self.selected_cog:
            await interaction.followup.send("❌ Cannot unload the Cog Manager itself.", ephemeral=True)
            return
        try:
            await self.bot.unload_extension(self.selected_cog)
            logger.info(f"Unloaded {self.selected_cog} by {interaction.user}")
            await interaction.followup.send(f"🔴 Unloaded `{self.selected_cog}`.", ephemeral=True)
        except commands.ExtensionNotLoaded:
            await interaction.followup.send("⚠️ Not currently loaded.", ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to unload {self.selected_cog}: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Failed to unload: `{e}`", ephemeral=True)
        await self._refresh(interaction)

    @discord.ui.button(label="Reload", style=discord.ButtonStyle.blurple, row=1)
    async def reload_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if not self.selected_cog:
            await interaction.followup.send("Select a cog first.", ephemeral=True)
            return
        try:
            await self.bot.reload_extension(self.selected_cog)
            logger.info(f"Reloaded {self.selected_cog} by {interaction.user}")
            await interaction.followup.send(f"🔄 Reloaded `{self.selected_cog}`.", ephemeral=True)
        except commands.ExtensionNotLoaded:
            await interaction.followup.send("⚠️ Not loaded — use Load instead.", ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to reload {self.selected_cog}: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Failed to reload: `{e}`", ephemeral=True)
        await self._refresh(interaction)

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.grey, row=1)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self._refresh(interaction)


class CogManagerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="cog", aliases=["cogs"])
    @commands.has_permissions(administrator=True)
    async def cog_manager(self, ctx: commands.Context):
        """Opens the interactive cog manager. (Admin only)"""
        view = CogManagerView(self.bot, ctx)
        await ctx.send(embed=build_status_embed(self.bot), view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(CogManagerCog(bot))
