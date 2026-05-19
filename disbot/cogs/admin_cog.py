from __future__ import annotations

import ast
import logging
import os
import re
import sys

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.interaction_helpers import help_ctx_shim, safe_defer, safe_edit
from utils.ui_constants import ADMIN_COLOR, INFO_COLOR, SUCCESS_COLOR
from views.base import HubView, send_panel

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
        with open(os.path.join(COGS_DIR, fname), encoding="utf-8") as fh:
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

    @commands.cooldown(rate=2, per=10, type=commands.BucketType.user)
    @commands.command(name="adminmenu")
    @commands.has_permissions(administrator=True)
    async def admin_menu(self, ctx):
        """Open the interactive admin control panel."""
        view = _AdminPanelView(ctx, self)
        await send_panel(ctx, embed=view.build_embed(), view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the admin control panel)."""
        view = _AdminPanelView(help_ctx_shim(interaction), self)
        return view.build_embed(), view

    # ------------------------------------------------------------------
    # Server Statistics
    # ------------------------------------------------------------------
    @commands.command(name="serverstats")
    @commands.has_permissions(administrator=True)
    async def server_stats(self, ctx):
        """Display server statistics."""
        guild = ctx.guild
        embed = discord.Embed(
            title=f"Server Stats for {guild.name}",
            color=SUCCESS_COLOR,
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
                f"❌ Invalid action `{action}`. Use `load`, `unload`, or `reload`.",
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
                f"❌ Unknown level `{level}`. Choose from: DEBUG, INFO, WARNING, ERROR, CRITICAL",
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
            channel = resources.resolve_channel(guild, name="bot_spam")
            if channel and channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(
                        f"Hello everyone! {self.bot.user.name} is now online and ready to rumble!",
                    )
                except Exception as e:
                    logging.error(f"Error sending startup message: {e}")


# ---------------------------------------------------------------------------
# Shared admin helpers
# ---------------------------------------------------------------------------


def attach_back_to_admin_button(
    view: discord.ui.View,
    author: discord.Member | discord.User,
) -> None:
    """Append a "↩ Back to Admin" control to a sub-view opened from the panel.

    Mirrors :func:`cogs.help_cog._attach_back_to_help_button`: the
    cog's panel class is not mutated — only the live view instance
    receives the extra button.  No-op if the view already has 25
    components (Discord cap).  When the back button is clicked a
    fresh ``_AdminPanelView`` is constructed so the embed reflects
    current cog load state.
    """
    if len(view.children) >= 25:
        logging.getLogger("bot.cogs.admin").warning(
            "Back-to-admin button skipped — %s already has 25 children.",
            type(view).__name__,
        )
        return

    back_btn = discord.ui.Button(  # type: ignore[var-annotated]
        label="↩ Back to Admin",
        custom_id="admin:back",
        style=discord.ButtonStyle.secondary,
        row=4,
    )

    async def _back_callback(interaction: discord.Interaction) -> None:
        cog = interaction.client.get_cog("AdminCog")  # type: ignore[attr-defined]
        if cog is None:
            await interaction.response.send_message(
                "Admin cog unavailable.",
                ephemeral=True,
            )
            return
        ctx_shim = help_ctx_shim(interaction)
        new_view = _AdminPanelView(ctx_shim, cog)  # type: ignore[arg-type]
        new_view._author = author  # preserve invoker identity
        await interaction.response.edit_message(
            embed=new_view.build_embed(),
            view=new_view,
        )

    back_btn.callback = _back_callback  # type: ignore[method-assign]
    view.add_item(back_btn)


# ---------------------------------------------------------------------------
# Admin Panel View
# ---------------------------------------------------------------------------


class _AdminPanelView(HubView):
    """Interactive admin control panel."""

    def __init__(self, ctx: commands.Context, cog: AdminCog):
        super().__init__(ctx.author)
        self.ctx = ctx
        self.cog = cog

    def build_embed(self) -> discord.Embed:
        loaded_count = len(self.cog.bot.extensions)
        embed = discord.Embed(
            title="🛠️ Admin Control Panel",
            description=(
                f"Loaded cogs: **{loaded_count}**\n\n"
                "**Tools**\n"
                "📊 Server Stats · 📋 Cog List · 🔄 Reload All · 📝 Log Level\n\n"
                "**Navigate**\n"
                "🛠 Settings · 🛰 Platform · 🩺 Diagnostics · 📝 Logging · "
                "🧹 Cleanup · 📚 Help"
            ),
            color=ADMIN_COLOR,
        )
        embed.set_footer(text="Only you can interact with this panel.")
        return embed

    @discord.ui.button(
        label="📊 Server Stats",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def stats_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"📊 Server Stats — {guild.name}",
            color=SUCCESS_COLOR,
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
            color=INFO_COLOR,
        )
        embed.set_footer(
            text="✅ Loaded  ❌ Unloaded  🟢 OK  🔴 Syntax Error  •  ↩ Overview to return",
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔄 Reload All", style=discord.ButtonStyle.grey, row=0)
    async def reload_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await interaction.client.is_owner(interaction.user):  # type: ignore[attr-defined]
            await interaction.response.send_message("Owner only.", ephemeral=True)
            return
        if not await safe_defer(interaction):
            return
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
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="📝 Log Level", style=discord.ButtonStyle.grey, row=0)
    async def loglevel_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.send_modal(_LogLevelModal(self))

    # ------------------------------------------------------------------
    # Row 1 — navigation to subsystem hubs (no logic duplicated; each
    # button delegates to the existing cog's panel/hook).
    # ------------------------------------------------------------------

    @discord.ui.button(label="🛠 Settings", style=discord.ButtonStyle.blurple, row=1)
    async def settings_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="SettingsCog")

    @discord.ui.button(label="🛰 Platform", style=discord.ButtonStyle.blurple, row=1)
    async def platform_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if not await safe_defer(interaction):
            return
        from views.diagnostic import _PlatformHubView, build_platform_hub_embed

        sub_view = _PlatformHubView(interaction.user)
        attach_back_to_admin_button(sub_view, interaction.user)
        await safe_edit(
            interaction,
            embed=build_platform_hub_embed(),
            view=sub_view,
        )

    @discord.ui.button(label="🩺 Diagnostics", style=discord.ButtonStyle.blurple, row=1)
    async def diagnostics_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="DiagnosticCog")

    @discord.ui.button(label="📝 Logging", style=discord.ButtonStyle.blurple, row=1)
    async def logging_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="LoggingCog")

    # ------------------------------------------------------------------
    # Row 2 — cleanup + help shortcuts
    # ------------------------------------------------------------------

    @discord.ui.button(label="🧹 Cleanup", style=discord.ButtonStyle.blurple, row=2)
    async def cleanup_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="Cleanup")

    @discord.ui.button(label="📚 Help", style=discord.ButtonStyle.blurple, row=2)
    async def help_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if not await safe_defer(interaction):
            return
        try:
            from cogs.help_cog import resolve_help_panel_state

            embed, new_view = await resolve_help_panel_state(interaction)
            await safe_edit(interaction, embed=embed, view=new_view)
        except Exception as exc:  # noqa: BLE001 — navigation must not crash panel
            logging.getLogger("bot.cogs.admin").warning(
                "Admin → Help navigation failed: %s",
                exc,
                exc_info=True,
            )
            embed = discord.Embed(
                title="Help unavailable",
                description=f"Could not open Help: `{type(exc).__name__}`.",
                color=discord.Color.orange(),
            )
            await safe_edit(interaction, embed=embed, view=self)

    # ------------------------------------------------------------------
    # Row 3 — overview anchor (rebuilds this panel in place)
    # ------------------------------------------------------------------

    @discord.ui.button(label="↩ Overview", style=discord.ButtonStyle.secondary, row=3)
    async def overview_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # ------------------------------------------------------------------
    # Shared helper for the three "open another cog's panel" buttons.
    # ------------------------------------------------------------------

    async def _open_via_help_hook(
        self,
        interaction: discord.Interaction,
        *,
        cog_name: str,
    ) -> None:
        """Open ``cog.build_help_menu_view(interaction)`` and edit in place.

        Mirrors the help cog's direct-navigation pattern: the target
        cog owns the panel; this panel just routes to it.  Adds a
        "↩ Back to Admin" button so the user can return.
        """
        if not await safe_defer(interaction):
            return
        cog = interaction.client.get_cog(cog_name)  # type: ignore[attr-defined]
        build_panel = getattr(cog, "build_help_menu_view", None) if cog else None
        if not callable(build_panel):
            embed = discord.Embed(
                title=f"{cog_name} unavailable",
                description=(
                    f"`{cog_name}` is not loaded or does not expose "
                    "`build_help_menu_view`."
                ),
                color=discord.Color.orange(),
            )
            await safe_edit(interaction, embed=embed, view=self)
            return
        try:
            sub_embed, sub_view = await build_panel(interaction)
        except Exception as exc:  # noqa: BLE001 — navigation must not crash panel
            logging.getLogger("bot.cogs.admin").warning(
                "Admin → %s navigation failed: %s",
                cog_name,
                exc,
                exc_info=True,
            )
            embed = discord.Embed(
                title=f"{cog_name} unavailable",
                description=f"Could not open `{cog_name}`: `{type(exc).__name__}`.",
                color=discord.Color.orange(),
            )
            await safe_edit(interaction, embed=embed, view=self)
            return
        attach_back_to_admin_button(sub_view, interaction.user)
        await safe_edit(interaction, embed=sub_embed, view=sub_view)


class _LogLevelModal(discord.ui.Modal, title="Set Log Level"):  # type: ignore[call-arg]
    level = discord.ui.TextInput(  # type: ignore[var-annotated]
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
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self.panel)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
