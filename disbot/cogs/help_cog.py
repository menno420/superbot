from __future__ import annotations
import discord
from discord.ext import commands
import logging

logger = logging.getLogger("bot")


def _clean_name(cog: commands.Cog) -> str:
    return cog.qualified_name.replace("Cog", "").strip()


def _get_visible_commands(cog: commands.Cog) -> list[commands.Command]:
    return [cmd for cmd in cog.get_commands() if not cmd.hidden and cmd.enabled]


def build_overview_embed(bot: commands.Bot) -> discord.Embed:
    embed = discord.Embed(
        title="📚 Help Menu",
        description="Select a category from the dropdown to see its commands.",
        color=discord.Color.blue(),
    )
    for cog in bot.cogs.values():
        cmds = _get_visible_commands(cog)
        if not cmds:
            continue
        names = " ".join(f"`{c.name}`" for c in cmds)
        embed.add_field(name=_clean_name(cog), value=names, inline=False)
    if not embed.fields:
        embed.description = "No commands currently loaded."
    return embed


def build_cog_embed(cog: commands.Cog, prefix: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"📖 {_clean_name(cog)}",
        color=discord.Color.blue(),
    )
    cmds = _get_visible_commands(cog)
    for cmd in cmds:
        aliases = f"  *(aliases: {', '.join(cmd.aliases)})*" if cmd.aliases else ""
        sig = f" {cmd.signature}".rstrip() if cmd.signature else ""
        usage = f"`{prefix}{cmd.name}{sig}`"
        desc = cmd.help or "No description."
        embed.add_field(
            name=f"`{prefix}{cmd.name}`{aliases}",
            value=f"{desc}\nUsage: {usage}",
            inline=False,
        )
    if not embed.fields:
        embed.description = "No commands in this category."
    return embed


class CategorySelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot):
        cogs_with_cmds = [
            cog for cog in bot.cogs.values() if _get_visible_commands(cog)
        ]
        options = [
            discord.SelectOption(
                label=_clean_name(cog),
                value=cog.qualified_name,
                description=f"{len(_get_visible_commands(cog))} command(s)",
            )
            for cog in cogs_with_cmds
        ][:25]
        super().__init__(
            placeholder="Choose a category…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view.ctx.author:
            await interaction.response.send_message("This help menu is not for you.", ephemeral=True)
            return
        cog = interaction.client.get_cog(self.values[0])
        if not cog:
            await interaction.response.send_message("That category is no longer loaded.", ephemeral=True)
            return
        prefix = self.view.prefix
        embed = build_cog_embed(cog, prefix)
        self.view.showing_cog = cog.qualified_name
        self.view.back_btn.disabled = False
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        super().__init__(timeout=300)
        self.bot = bot
        self.ctx = ctx
        self.showing_cog: str | None = None
        self.prefix = ctx.prefix or "!"
        self._select = CategorySelect(bot)
        self.add_item(self._select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This help menu is not for you.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, row=1, disabled=True)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.showing_cog = None
        button.disabled = True
        # Rebuild select so it reflects currently loaded cogs
        self.remove_item(self._select)
        self._select = CategorySelect(self.bot)
        self.add_item(self._select)
        await interaction.response.edit_message(embed=build_overview_embed(self.bot), view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help", aliases=["hilfe"])
    async def help_command(self, ctx: commands.Context, *, category: str = None):
        """Shows all available commands. Pass a category name for details."""
        if category:
            cog = self.bot.get_cog(category) or self.bot.get_cog(category + "Cog")
            cmd = self.bot.get_command(category)
            if cog:
                embed = build_cog_embed(cog, ctx.prefix or "!")
                await ctx.send(embed=embed, delete_after=60)
                return
            if cmd:
                prefix = ctx.prefix or "!"
                embed = discord.Embed(
                    title=f"`{prefix}{cmd.name}`",
                    description=cmd.help or "No description.",
                    color=discord.Color.green(),
                )
                if cmd.aliases:
                    embed.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in cmd.aliases))
                embed.add_field(
                    name="Usage",
                    value=f"`{prefix}{cmd.name}{(' ' + cmd.signature) if cmd.signature else ''}`",
                    inline=False,
                )
                await ctx.send(embed=embed, delete_after=60)
                return
            await ctx.send(f"No command or category named `{category}` found.", delete_after=10)
            return

        view = HelpView(self.bot, ctx)
        embed = build_overview_embed(self.bot)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
    logger.info("HelpCog loaded.")
