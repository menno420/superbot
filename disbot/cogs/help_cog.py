import discord
from discord.ext import commands
import logging
import json
import os
from utils.localization import localization  # Import localization system

# Configure logging
logger = logging.getLogger(__name__)

# Path to localization file
LOCALIZATION_PATH = "/home/menno/disbot/data/json/localization.json"

def get_command_language(ctx):
    """Detects language based on invoked alias."""
    return "de" if ctx.invoked_with == "hilfe" else "en"

def load_translations():
    """Loads command descriptions from localization.json."""
    if not os.path.exists(LOCALIZATION_PATH):
        return {"en": {}, "de": {}}

    try:
        with open(LOCALIZATION_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        logger.error("❌ Error: localization.json is corrupted.")
        return {"en": {}, "de": {}}
    except Exception as e:
        logger.error(f"❌ Unexpected error while loading translations: {e}")
        return {"en": {}, "de": {}}

translations = load_translations()

class HelpCog(commands.Cog):
    """A custom help command cog with bilingual support."""

    def __init__(self, bot):
        self.bot = bot

    def get_prefix(self, ctx):
        prefixes = self.bot.command_prefix
        return prefixes[0] if isinstance(prefixes, list) else prefixes

    @commands.command(name="help", aliases=["hilfe"])
    async def help_command(self, ctx, *, command_or_category: str = None):
        """Displays available categories or commands in a specific category."""
        lang = get_command_language(ctx)
        logger.info(f"Help command invoked by {ctx.author} in language: {lang}")

        if command_or_category:
            await self.send_specific_help(ctx, command_or_category, lang)
        else:
            await self.send_general_help(ctx, lang)

    async def send_specific_help(self, ctx, command_or_category, lang):
        """Provides detailed help for a specific command or category."""
        try:
            command = self.bot.get_command(command_or_category)
            if command:
                cmd_key = f"cmd_{command.name}"
                description = translations.get(lang, {}).get(cmd_key)

                if not description:
                    logger.warning(f"⚠️ Missing translation for '{cmd_key}' in '{lang}', falling back to English.")
                    description = translations.get("en", {}).get(cmd_key, localization.get("no_desc", "en"))

                embed = discord.Embed(
                    title=localization.get("help_command_title", lang, command=command.name),
                    description=localization.get("help_command_desc", lang, description=description, usage=f"{self.get_prefix(ctx)}{command.name} {command.signature}"),
                    color=discord.Color.green(),
                )
                if command.aliases:
                    alias_text = ", ".join(command.aliases)
                    embed.add_field(name=localization.get("aliases", lang), value=alias_text, inline=False)
                embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
                embed.set_footer(text=localization.get("requested_by", lang, user=ctx.author), icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

                await ctx.send(embed=embed, delete_after=60)
                return

            # Check if it's a cog
            cog = self.bot.get_cog(command_or_category)
            if cog:
                commands_list = [
                    f"**{cmd.name}** (Aliases: {', '.join(cmd.aliases) if cmd.aliases else 'None'})\n"
                    f"{translations.get(lang, {}).get(f'cmd_{cmd.name}', localization.get('no_desc', lang))}"
                    for cmd in cog.get_commands()
                    if not cmd.hidden and cmd.enabled and await cmd.can_run(ctx)
                ]

                if commands_list:
                    description = "\n\n".join(commands_list)
                    embed = discord.Embed(
                        title=localization.get("help_cog_title", lang, cog=cog.qualified_name.replace("Cog", "")),
                        description=description,
                        color=discord.Color.blue(),
                    )
                    embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
                    embed.set_footer(text=localization.get("requested_by", lang, user=ctx.author), icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
                    await ctx.send(embed=embed, delete_after=60)
                else:
                    await ctx.send(localization.get("no_commands_in_cog", lang, cog=cog.qualified_name.replace("Cog", "")), delete_after=10)
                return

            await ctx.send(localization.get("not_found", lang, name=command_or_category), delete_after=10)
        except Exception as e:
            logger.error(f"❌ ERROR in send_specific_help: {type(e).__name__} - {e}", exc_info=True)
            await ctx.send(f"⚠️ Debug: `{type(e).__name__} - {e}`", delete_after=15)

    async def send_general_help(self, ctx, lang):
        """Displays general help with available cogs."""
        try:
            cogs = [cog for _, cog in self.bot.cogs.items()]
            if not cogs:
                await ctx.send(localization.get("no_categories", lang), delete_after=10)
                return

            view = HelpCategoryView(self, ctx, cogs, lang)

            embed = discord.Embed(
                title=localization.get("help_categories", lang),
                description=localization.get("help_intro", lang),
                color=discord.Color.blue(),
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
            embed.set_footer(text=localization.get("requested_by", lang, user=ctx.author), icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

            await ctx.send(embed=embed, view=view, delete_after=None)
        except Exception as e:
            logger.error(f"❌ ERROR in send_general_help: {type(e).__name__} - {e}", exc_info=True)
            await ctx.send(f"⚠️ Debug: `{type(e).__name__} - {e}`", delete_after=15)

# ==========================
# Help Category Button View
# ==========================
class HelpCategoryView(discord.ui.View):
    """A View that contains buttons for each help category (cog)."""

    def __init__(self, cog, ctx, cogs, lang):
        super().__init__(timeout=180)
        self.cog = cog
        self.ctx = ctx
        self.cogs = cogs
        self.lang = lang

        # Assign buttons dynamically
        for cog in self.cogs:
            clean_name = cog.qualified_name.replace("Cog", "")  # Remove 'Cog' from name
            button = discord.ui.Button(label=clean_name, style=discord.ButtonStyle.primary)
            button.callback = self.make_category_callback(cog)
            self.add_item(button)

    def make_category_callback(self, cog):
        """Creates an asynchronous callback for category buttons."""
        async def category_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message(
                    localization.get("not_your_help_menu", self.lang), ephemeral=True
                )
                return

            await interaction.response.defer()

            commands_list = [
                f"**{cmd.name}** (Aliases: {', '.join(cmd.aliases) if cmd.aliases else 'None'})\n{cmd.help or localization.get('no_desc', self.lang)}"
                for cmd in cog.get_commands()
                if not cmd.hidden and cmd.enabled
            ]

            if commands_list:
                description = "\n\n".join(commands_list)
                embed = discord.Embed(
                    title=localization.get("help_cog_title", self.lang, cog=cog.qualified_name.replace("Cog", "")),
                    description=description,
                    color=discord.Color.blue(),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    localization.get("no_commands_in_cog", self.lang, cog=cog.qualified_name.replace("Cog", "")),
                    ephemeral=True
                )

        return category_callback

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
    logger.info("HelpCog loaded successfully.")