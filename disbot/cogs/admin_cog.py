from __future__ import annotations

import logging
import os
import sys

import discord
from discord import app_commands
from discord.ext import commands

from cogs.admin.cog_manager import (  # noqa: F401 — re-exported for back-compat (callers may import here)
    COGS_DIR,
    _all_cog_modules,
    _CogManagerView,
    _do_load,
    _do_reload,
    _do_unload,
    _find_module,
)
from core.runtime import resources
from core.runtime.interaction_helpers import help_ctx_shim, safe_defer, safe_edit
from utils.ui_constants import ADMIN_COLOR, INFO_COLOR, SUCCESS_COLOR  # noqa: F401
from views.base import HubView, send_panel

PID_FILE = os.path.join(os.path.dirname(COGS_DIR), "bot.pid")


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

    @app_commands.command(
        name="admin",
        description="Open the Admin control panel (administrator only).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def admin_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door for the Admin hub — ephemeral, admin-only.

        PR E2 — privileged slash. ``default_permissions`` hides the
        command from non-admins in the Discord UI; ``checks.has_permissions``
        enforces at runtime. Both layers are kept so the gate works
        whether or not the guild's Discord client is up to date.
        """
        embed, view = await self.build_help_menu_view(interaction)
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )

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
        """Load, unload, or reload a cog by name (underscores and _cog suffix optional).

        The prefix command intentionally retains no critical-cog
        protection — it is the operator's escape hatch when the panel
        won't open or a protected cog needs to be unloaded. The panel
        Unload button refuses protected cogs (see ``_PROTECTED_COGS``).
        """
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
        if action == "load":
            await ctx.send(await _do_load(self.bot, module))
        elif action == "unload":
            await ctx.send(await _do_unload(self.bot, module))
        else:  # action == "reload"
            await ctx.send(await _do_reload(self.bot, module))

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
    # Slash-command tree sync + diagnostics (PR E')
    # ------------------------------------------------------------------
    @commands.command(name="syncslash", aliases=["syncs"])
    @commands.is_owner()
    async def sync_slash_commands(
        self,
        ctx: commands.Context,
        scope: str = "guild",
    ) -> None:
        """Sync the app-command tree for slash commands (owner only).

        PR E' — operator tooling for the post-deploy resync workflow.
        After PR E1 / E2 add or change slash commands, the Discord
        command tree needs to be told about them. This command lets
        operators trigger that sync workflow on demand.

        Usage::

            !syncslash             # sync this guild (default — fast)
            !syncslash guild       # sync this guild (explicit)
            !syncslash global      # sync globally — rate-limited;
                                   #   propagation can take up to 1 h

        ``guild`` scope is the right choice in almost every case:
        Discord rate-limits global sync, and per-guild sync makes
        new commands appear immediately. ``global`` is only needed
        if the bot deploys to a guild that hasn't seen the tree yet.
        """
        scope = scope.lower()
        if scope not in ("guild", "global"):
            await ctx.send("❌ Invalid scope. Use `guild` or `global`.")
            return

        if scope == "global":
            try:
                synced = await self.bot.tree.sync()
            except discord.HTTPException as exc:
                await ctx.send(
                    f"⚠️ Global sync failed: `{type(exc).__name__}`: {exc}",
                )
                return
            await ctx.send(
                f"✅ Synced **{len(synced)}** slash commands globally. "
                "Propagation may take up to an hour.",
            )
            return

        guild = ctx.guild
        if guild is None:
            await ctx.send("❌ `guild` scope requires a guild context.")
            return
        try:
            self.bot.tree.copy_global_to(guild=guild)
            synced = await self.bot.tree.sync(guild=guild)
        except discord.HTTPException as exc:
            await ctx.send(
                f"⚠️ Guild sync failed: `{type(exc).__name__}`: {exc}",
            )
            return
        await ctx.send(
            f"✅ Copied global slash commands and synced **{len(synced)}** commands "
            f"to **{guild.name}**.",
        )

    @commands.command(name="slashes", aliases=["slashlist"])
    @commands.has_permissions(administrator=True)
    async def list_slash_commands(
        self,
        ctx: commands.Context,
        scope: str = "guild",
    ) -> None:
        """List currently-registered slash commands (admin only).

        PR E' — read-only deployment diagnostic. Useful for
        confirming after a sync that the expected commands are
        present, and for spotting drift between code (what's
        decorated with ``@app_commands.command``) and what Discord
        actually has registered.

        Usage::

            !slashes           # this guild (default)
            !slashes guild     # this guild (explicit)
            !slashes global    # global tree

        Listing reads from the bot's in-memory tree (what code has
        registered), not from Discord — so it reflects the current
        process's state regardless of whether a sync has propagated
        yet.
        """
        scope = scope.lower()
        if scope not in ("guild", "global"):
            await ctx.send("❌ Invalid scope. Use `guild` or `global`.")
            return

        if scope == "global":
            commands_list = list(self.bot.tree.get_commands())
            title = "📋 Global Slash Commands"
        else:
            guild = ctx.guild
            if guild is None:
                await ctx.send("❌ `guild` scope requires a guild context.")
                return
            commands_list = list(self.bot.tree.get_commands(guild=guild))
            title = f"📋 Guild Slash Commands — {guild.name}"

        if not commands_list:
            if scope == "guild":
                await ctx.send(
                    "_No guild-local slash commands registered._ "
                    "Most slash commands may be in the global tree. "
                    "Use `!syncslash guild` to copy global commands into this guild "
                    "and sync them immediately.",
                )
            else:
                await ctx.send("_No global slash commands registered._")
            return

        ordered = sorted(commands_list, key=lambda c: c.name)
        lines = [
            f"`/{cmd.name}` — {cmd.description or '_no description_'}"
            for cmd in ordered
        ]
        embed = discord.Embed(
            title=title,
            description="\n".join(lines),
            color=INFO_COLOR,
        )
        embed.set_footer(text=f"{len(commands_list)} commands.")
        await ctx.send(embed=embed)

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
        """Open the interactive cog manager (PR C).

        Replaces the previous read-only embed. Owners can load /
        unload / reload from the panel; non-owners see the same
        status surface but mutation buttons deny. Protected core
        cogs (``_PROTECTED_COGS``) refuse unload from the panel —
        prefix ``!cog unload`` retains no protection as the
        operator's escape hatch.
        """
        view = _CogManagerView(self.cog, self._author)
        attach_back_to_admin_button(view, self._author)
        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view,
        )

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
