from __future__ import annotations

import ast
import asyncio
import logging
import os
import re
import sys

import discord
from discord.ext import commands
from utils.ui_constants import ADMIN_COLOR
from views.base import BaseView

COGS_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(os.path.dirname(COGS_DIR), "bot.pid")


def _normalize(name: str) -> str:
    """Strip underscores/spaces, lowercase, remove trailing 'cog'."""
    return re.sub(r"[\s_]+", "", name.lower()).removesuffix("cog")


def _find_module(name: str) -> str | None:
    """Return the full module path (e.g. 'cogs.admin_cog') for a fuzzy cog name."""
    target = _normalize(name)
    for fname in sorted(os.listdir(COGS_DIR)):
        if fname.endswith("_cog.py") and not fname.startswith("__"):
            if _normalize(fname[:-3]) == target:
                return f"cogs.{fname[:-3]}"
    return None


def _all_cog_modules() -> list[str]:
    """Return module paths for every *_cog.py file."""
    return [
        f"cogs.{f[:-3]}"
        for f in sorted(os.listdir(COGS_DIR))
        if f.endswith("_cog.py") and not f.startswith("__")
    ]


def _syntax_ok(fname: str) -> bool:
    """Return True if the file parses without syntax errors."""
    try:
        with open(os.path.join(COGS_DIR, fname), "r", encoding="utf-8") as fh:
            ast.parse(fh.read(), fname)
        return True
    except SyntaxError:
        return False


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # Admin menu
    # ------------------------------------------------------------------

    @commands.command(name="adminmenu")
    @commands.has_permissions(administrator=True)
    async def admin_menu(self, ctx):
        """Open the interactive admin control panel."""
        view = _AdminPanelView(ctx, self)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg

    # ------------------------------------------------------------------
    # Server Statistics
    # ------------------------------------------------------------------
    @commands.command(name="serverstats")
    @commands.has_permissions(administrator=True)
    async def server_stats(self, ctx):
        """Display server statistics."""
        guild = ctx.guild
        embed = discord.Embed(
            title=f"Server Stats for {guild.name}", color=discord.Color.green()
        )
        embed.add_field(name="Total Members", value=guild.member_count)
        embed.add_field(
            name="Online Members",
            value=sum(m.status != discord.Status.offline for m in guild.members),
        )
        embed.add_field(name="Text Channels", value=len(guild.text_channels))
        embed.add_field(name="Voice Channels", value=len(guild.voice_channels))
        embed.add_field(name="Roles", value=len(guild.roles))
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Cog Management
    # ------------------------------------------------------------------
    @commands.command(name="cog")
    @commands.is_owner()
    async def manage_cog(self, ctx, action: str, cog_name: str):
        """Load, unload, or reload a cog by name (underscores and _cog suffix optional)."""
        action = action.lower()
        if action not in ("load", "unload", "reload"):
            await ctx.send(
                f"❌ Invalid action `{action}`. Use `load`, `unload`, or `reload`."
            )
            return
        module = _find_module(cog_name)
        if not module:
            await ctx.send(f"❌ No cog found matching `{cog_name}`.")
            return
        try:
            if action == "load":
                await self.bot.load_extension(module)
            elif action == "unload":
                await self.bot.unload_extension(module)
            elif action == "reload":
                await self.bot.reload_extension(module)
            await ctx.send(f"✅ `{module}` {action}ed.")
        except Exception as e:
            await ctx.send(f"⚠️ Error {action}ing `{module}`: {e}")

    @commands.command(name="loadall")
    @commands.is_owner()
    async def load_all_cogs(self, ctx):
        """Load all unloaded cogs, skipping already-loaded ones."""
        loaded_now, skipped, failed = [], [], []
        for module in _all_cog_modules():
            if module in self.bot.extensions:
                skipped.append(module.split(".")[1])
                continue
            try:
                await self.bot.load_extension(module)
                loaded_now.append(module.split(".")[1])
            except Exception as e:
                failed.append(f'`{module.split(".")[1]}`: {e}')
        parts = []
        if loaded_now:
            parts.append(f'✅ Loaded: {", ".join(f"`{n}`" for n in loaded_now)}')
        if skipped:
            parts.append(f'⏭️ Already loaded: {", ".join(f"`{n}`" for n in skipped)}')
        if failed:
            parts.append("❌ Failed:\n" + "\n".join(failed))
        await ctx.send("\n".join(parts) or "✅ Nothing to load.")

    @commands.command(name="unloadall")
    @commands.is_owner()
    async def unload_all_cogs(self, ctx):
        """Unload all loaded cogs except this one."""
        unloaded, skipped, failed = [], [], []
        for module in _all_cog_modules():
            if module == "cogs.admin_cog":
                skipped.append("admin_cog (self)")
                continue
            if module not in self.bot.extensions:
                skipped.append(module.split(".")[1])
                continue
            try:
                await self.bot.unload_extension(module)
                unloaded.append(module.split(".")[1])
            except Exception as e:
                failed.append(f'`{module.split(".")[1]}`: {e}')
        parts = []
        if unloaded:
            parts.append(f'🔴 Unloaded: {", ".join(f"`{n}`" for n in unloaded)}')
        if skipped:
            parts.append(f'⏭️ Skipped: {", ".join(f"`{n}`" for n in skipped)}')
        if failed:
            parts.append("❌ Failed:\n" + "\n".join(failed))
        await ctx.send("\n".join(parts) or "✅ Nothing to unload.")

    # ------------------------------------------------------------------
    # Restart
    # ------------------------------------------------------------------
    @commands.command(name="restart")
    @commands.is_owner()
    async def reload_main_script(self, ctx):
        """Restart the bot process."""
        await ctx.send("♻️ Restarting bot...")
        logging.info("Restarting bot...")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        await self.bot.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    # ------------------------------------------------------------------
    # Webhook log level
    # ------------------------------------------------------------------
    @commands.command(name="loglevel")
    @commands.has_permissions(administrator=True)
    async def set_log_level(self, ctx, level: str):
        """Change the bot log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)."""
        level_int = getattr(logging, level.upper(), None)
        if not isinstance(level_int, int):
            await ctx.send(
                f"❌ Unknown level `{level}`. Choose from: DEBUG, INFO, WARNING, ERROR, CRITICAL"
            )
            return
        logging.getLogger().setLevel(level_int)
        await ctx.send(f"✅ Log level set to `{level.upper()}`.")

    # ------------------------------------------------------------------
    # Startup message
    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name="bot_spam")
            if channel and channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(
                        f"Hello everyone! {self.bot.user.name} is now online and ready to rumble!"
                    )
                except Exception as e:
                    logging.error(f"Error sending startup message: {e}")


# ---------------------------------------------------------------------------
# Admin Panel View
# ---------------------------------------------------------------------------


class _AdminPanelView(BaseView):
    """Interactive admin control panel."""

    def __init__(self, ctx: commands.Context, cog: AdminCog):
        super().__init__(ctx.author, timeout=180)
        self.ctx = ctx
        self.cog = cog

    def build_embed(self) -> discord.Embed:
        loaded_count = len(self.cog.bot.extensions)
        embed = discord.Embed(
            title="🛠️ Admin Control Panel",
            description=(
                f"Loaded cogs: **{loaded_count}**\n\n"
                "**📊 Server Stats** — member & channel statistics\n"
                "**📋 Cog List** — all cogs with load status\n"
                "**🔄 Reload All** — reload all loaded cogs (owner)\n"
                "**📝 Log Level** — change the bot log level"
            ),
            color=ADMIN_COLOR,
        )
        embed.set_footer(text="Only you can interact with this panel.")
        return embed

    @discord.ui.button(
        label="📊 Server Stats", style=discord.ButtonStyle.blurple, row=0
    )
    async def stats_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"📊 Server Stats — {guild.name}", color=discord.Color.green()
        )
        embed.add_field(name="Total Members", value=str(guild.member_count))
        embed.add_field(
            name="Online Members",
            value=str(sum(m.status != discord.Status.offline for m in guild.members)),
        )
        embed.add_field(name="Text Channels", value=str(len(guild.text_channels)))
        embed.add_field(name="Voice Channels", value=str(len(guild.voice_channels)))
        embed.add_field(name="Roles", value=str(len(guild.roles)))
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="📋 Cog List", style=discord.ButtonStyle.blurple, row=0)
    async def coglist_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        loaded = set(self.cog.bot.extensions.keys())
        lines = []
        for fname in sorted(os.listdir(COGS_DIR)):
            if not fname.endswith("_cog.py") or fname.startswith("__"):
                continue
            module = f"cogs.{fname[:-3]}"
            load_icon = "✅" if module in loaded else "❌"
            syntax_icon = "🟢" if _syntax_ok(fname) else "🔴"
            lines.append(f"{load_icon} {syntax_icon}  `{fname[:-3]}`")
        embed = discord.Embed(
            title="📋 Cog List",
            description="\n".join(lines) or "No cogs found.",
            color=discord.Color.blue(),
        )
        embed.set_footer(
            text="✅ Loaded  ❌ Unloaded  🟢 OK  🔴 Syntax Error  •  ↩ Overview to return"
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔄 Reload All", style=discord.ButtonStyle.grey, row=0)
    async def reload_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await interaction.client.is_owner(interaction.user):
            await interaction.response.send_message("Owner only.", ephemeral=True)
            return
        await interaction.response.defer()
        reloaded, failed = [], []
        for module in list(self.cog.bot.extensions.keys()):
            try:
                await self.cog.bot.reload_extension(module)
                reloaded.append(module.split(".")[1])
            except Exception as e:
                failed.append(f'`{module.split(".")[1]}`: {e}')
        parts = []
        if reloaded:
            parts.append(f'🔄 Reloaded: {", ".join(f"`{n}`" for n in reloaded)}')
        if failed:
            parts.append("❌ Failed:\n" + "\n".join(failed))
        embed = discord.Embed(
            title="🔄 Reload Complete",
            description="\n".join(parts) or "Nothing reloaded.",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="📝 Log Level", style=discord.ButtonStyle.grey, row=0)
    async def loglevel_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ):
        await interaction.response.send_modal(_LogLevelModal(self))

    @discord.ui.button(label="↩ Overview", style=discord.ButtonStyle.secondary, row=1)
    async def overview_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ):
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


class _LogLevelModal(discord.ui.Modal, title="Set Log Level"):  # type: ignore[call-arg]
    level = discord.ui.TextInput(
        label="Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)",
        placeholder="INFO",
        max_length=10,
    )

    def __init__(self, panel: _AdminPanelView):
        super().__init__()
        self.panel = panel

    async def on_submit(self, interaction: discord.Interaction):
        level_int = getattr(logging, self.level.value.upper(), None)
        if not isinstance(level_int, int):
            await interaction.response.send_message(
                f"❌ Unknown level `{self.level.value.upper()}`. "
                "Choose from: DEBUG, INFO, WARNING, ERROR, CRITICAL",
                ephemeral=True,
            )
            return
        logging.getLogger().setLevel(level_int)
        embed = discord.Embed(
            title="📝 Log Level Updated",
            description=f"Log level set to `{self.level.value.upper()}`.",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self.panel)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
