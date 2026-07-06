from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.admin import _slash_sync
from cogs.admin.cog_manager import (  # noqa: F401 — re-exported for back-compat (callers may import here)
    COGS_DIR,
    _all_cog_modules,
    _CogManagerView,
    _do_load,
    _do_reload,
    _do_unload,
    _emit_admin_runtime_audit,
    _find_module,
    _LogLevelModal,
)
from core.runtime import lifecycle, resources
from core.runtime.interaction_helpers import help_ctx_shim, safe_defer, safe_edit
from core.runtime.permission_checks import admin_or_owner, app_admin_or_owner
from utils.ui_constants import ADMIN_COLOR, INFO_COLOR, SUCCESS_COLOR  # noqa: F401
from views.base import HubView, send_panel
from views.navigation import attach_back_button, help_nav_attachments


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # Admin menu
    # ------------------------------------------------------------------

    @commands.cooldown(rate=2, per=10, type=commands.BucketType.user)
    @commands.command(name="adminmenu")
    @admin_or_owner()
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
    @app_admin_or_owner()
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
    @admin_or_owner()
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
        actor_id = getattr(ctx.author, "id", None)
        if action == "load":
            await ctx.send(await _do_load(self.bot, module, actor_id=actor_id))
        elif action == "unload":
            await ctx.send(await _do_unload(self.bot, module, actor_id=actor_id))
        else:  # action == "reload"
            await ctx.send(await _do_reload(self.bot, module, actor_id=actor_id))

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
                failed.append(f"`{module.split('.')[1]}`: {e}")
        parts = []
        if loaded_now:
            parts.append(f"✅ Loaded: {', '.join(f'`{n}`' for n in loaded_now)}")
        if skipped:
            parts.append(f"⏭️ Already loaded: {', '.join(f'`{n}`' for n in skipped)}")
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
                failed.append(f"`{module.split('.')[1]}`: {e}")
        parts = []
        if unloaded:
            parts.append(f"🔴 Unloaded: {', '.join(f'`{n}`' for n in unloaded)}")
        if skipped:
            parts.append(f"⏭️ Skipped: {', '.join(f'`{n}`' for n in skipped)}")
        if failed:
            parts.append("❌ Failed:\n" + "\n".join(failed))
        await ctx.send("\n".join(parts) or "✅ Nothing to unload.")

    @commands.cooldown(rate=2, per=10, type=commands.BucketType.user)
    @commands.command(
        name="coglist",
        aliases=["cogs", "listcogs", "cogslist"],
        # Fluency spellings users actually type (the BUG-0014 report showed
        # both !cogs and !coglist) — visible by contract, not compat shims.
        extras={"alias_classification": "power_user_shortcut"},
    )
    @admin_or_owner()
    async def coglist_command(self, ctx):
        """Open the interactive cog manager — the panel's 📋 Cog List button.

        Mirrors ``_AdminPanelView`` → "📋 Cog List": posts the same
        ``_CogManagerView`` (loaded / unloaded / syntax status for every
        cog) so the text command and the button share one surface. Admins
        can view the list; mutations stay owner-gated by the view itself
        (non-owners' Load/Unload/Reload buttons deny). The prefix ``!cog``
        command remains the unprotected escape hatch for mutations.
        """
        view = _CogManagerView(self, ctx.author)
        await send_panel(ctx, embed=view.build_embed(), view=view)

    # ------------------------------------------------------------------
    # Slash-command tree sync + diagnostics (PR E')
    # ------------------------------------------------------------------
    @commands.command(name="syncslash", aliases=["syncs"])
    @commands.is_owner()
    async def sync_slash_commands(
        self,
        ctx: commands.Context,
        scope: str = "guild",
        modifier: str = "",
    ) -> None:
        """Sync the app-command tree for slash commands (owner only).

        PR E' — operator tooling for the post-deploy resync workflow.
        After PR E1 / E2 add or change slash commands, the Discord
        command tree needs to be told about them. This command lets
        operators trigger that sync workflow on demand.

        Usage::

            !syncslash             # sync this guild (default — fast)
            !syncslash guild       # sync this guild (explicit)
            !syncslash global      # sync globally IFF the tree changed —
                                   #   previews the diff, skips when in sync
            !syncslash global force  # sync globally unconditionally (cosmetic
                                     #   param/description-only changes)
            !syncslash clear       # remove this guild's command COPIES

        ``guild`` scope is the right choice in almost every case:
        Discord rate-limits global sync, and per-guild sync makes
        new commands appear immediately. ``global`` is only needed
        if the bot deploys to a guild that hasn't seen the tree yet.

        The ``global`` path now flows through the same diff-gated helper as the
        startup auto-sync (``command_tree_sync.auto_sync_if_changed``): it fetches
        the live global commands, compares command *paths* to the local tree, and
        only calls ``tree.sync()`` when they differ — reporting the add/remove
        diff or a clean "already in sync". The path-diff deliberately misses
        parameter/description-only edits (Discord normalises option payloads), so
        ``global force`` keeps the old unconditional sync for those cosmetic cases.

        **Do not run ``guild`` and ``global`` for the same environment.**
        A command synced *both* globally and into a guild renders **twice**
        in that guild (once from the global set, once from the guild-local
        copy ``copy_global_to`` makes). Pick one — ``global`` for production,
        ``guild`` for instant dev — and use ``clear`` to drop the guild
        copies if you end up with the duplicate listing.
        """
        scope = scope.lower()
        if scope not in ("guild", "global", "clear"):
            await ctx.send("❌ Invalid scope. Use `guild`, `global`, or `clear`.")
            return

        if scope == "global":
            message = await _slash_sync.run_global_sync(
                self.bot,
                force=modifier.lower() == "force",
            )
            await ctx.send(message)
            return

        guild = ctx.guild
        if guild is None:
            await ctx.send("❌ `guild` / `clear` scope requires a guild context.")
            return

        if scope == "clear":
            # Drop the guild-local command copies so each command renders once
            # again (from the global set). The fix for the "every command shows
            # twice" state you get from syncing both globally and to the guild.
            try:
                self.bot.tree.clear_commands(guild=guild)
                await self.bot.tree.sync(guild=guild)
            except discord.HTTPException as exc:
                await ctx.send(
                    f"⚠️ Clear failed: `{type(exc).__name__}`: {exc}",
                )
                return
            await ctx.send(
                f"✅ Cleared **{guild.name}**'s guild-local command copies. If the "
                "commands were also synced globally, each now shows once "
                "(global propagation can take up to an hour to settle).",
            )
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
            f"to **{guild.name}**. ⚠️ If you also ran `!syncslash global`, this guild "
            "now shows each command twice — run `!syncslash clear` to drop these "
            "guild copies and keep the global set.",
        )

    @commands.command(name="slashes", aliases=["slashlist"])
    @admin_or_owner()
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
        """Request a graceful restart through the lifecycle service.

        LP-3: the cog no longer owns process control. It records intent
        via :func:`core.runtime.lifecycle.request_restart`; a watchdog in
        ``bot1.py`` turns the request into ``bot.close()`` with a bounded
        timeout, the ``main()`` finally block runs cleanup, and the
        process exits cleanly so the orchestration platform respawns it.
        Repeated ``!restart`` calls during drain coalesce — only the
        first caller wins.
        """
        accepted = lifecycle.request_restart(
            reason="!restart",
            actor=str(ctx.author),
        )
        if accepted:
            await ctx.send("♻️ Restart requested. Bot is closing for restart.")
            logging.info("Restart requested by %s", ctx.author)
            await _emit_admin_runtime_audit(
                "restart",
                "runtime:process",
                None,
                "!restart",
                getattr(ctx.author, "id", None),
            )
        else:
            await ctx.send(
                "⚠️ A shutdown or restart is already in progress — request coalesced.",
            )

    # ------------------------------------------------------------------
    # Webhook log level
    # ------------------------------------------------------------------
    @commands.command(name="loglevel")
    @admin_or_owner()
    async def set_log_level(self, ctx, level: str):
        """Change the bot log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)."""
        level_int = getattr(logging, level.upper(), None)
        if not isinstance(level_int, int):
            await ctx.send(
                f"❌ Unknown level `{level}`. Choose from: DEBUG, INFO, WARNING, ERROR, CRITICAL",
            )
            return
        old_level = logging.getLevelName(logging.getLogger().level)
        logging.getLogger().setLevel(level_int)
        await ctx.send(f"✅ Log level set to `{level.upper()}`.")
        await _emit_admin_runtime_audit(
            "set_log_level",
            "logging:root",
            old_level,
            level.upper(),
            getattr(ctx.author, "id", None),
        )

    # ------------------------------------------------------------------
    # Startup message
    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            channel = resources.resolve_channel(guild, name="bot-spam")
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

    Thin wrapper around
    :func:`disbot.views.navigation.attach_back_button` — the parent
    builder constructs a fresh ``_AdminPanelView`` at click time so
    the embed reflects current cog-load state.  No-op if the view is
    already at the 25-component Discord cap (``attach_back_button``
    logs and returns False in that case).
    """

    async def _build_admin_parent(
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        cog = interaction.client.get_cog("AdminCog")  # type: ignore[attr-defined]
        if cog is None:
            raise RuntimeError("Admin cog unavailable.")
        ctx_shim = help_ctx_shim(interaction)
        new_view = _AdminPanelView(ctx_shim, cog)  # type: ignore[arg-type]
        new_view._author = author  # preserve invoker identity
        return new_view.build_embed(), new_view

    attach_back_button(
        view,
        label="↩ Back to Admin",
        custom_id="admin:back",
        parent_builder=_build_admin_parent,
        row=4,
        error_message="Admin cog unavailable — please try again.",
    )


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
            title="⚙️ Server & Admin",
            description=(
                f"Loaded cogs: **{loaded_count}**\n\n"
                "**Tools**\n"
                "📊 Server Stats · 📋 Cog List · 🔄 Reload All · 📝 Log Level\n\n"
                "**Configure & Operate**\n"
                "🛠 Settings · 🧭 Server Management · 📐 Channels · 🤖 AI\n\n"
                "**Platform & Diagnostics**\n"
                "🛰 Platform · 🩺 Diagnostics · 🧪 UX Lab · 📝 Logging · 🧹 Cleanup\n\n"
                "📚 Help"
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
                failed.append(f"`{module.split('.')[1]}`: {e}")
        parts = []
        if reloaded:
            parts.append(f"🔄 Reloaded: {', '.join(f'`{n}`' for n in reloaded)}")
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
    # Row 1 — Configure & Operate: the Server & Admin hub's primary children
    # (help-menu regrouping, PR #1290). No logic duplicated; each button
    # delegates to the child cog's build_help_menu_view hook.
    # ------------------------------------------------------------------

    @discord.ui.button(label="🛠 Settings", style=discord.ButtonStyle.blurple, row=1)
    async def settings_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="SettingsCog")

    @discord.ui.button(
        label="🧭 Server Management",
        style=discord.ButtonStyle.blurple,
        row=1,
    )
    async def server_management_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="ServerManagementCog")

    @discord.ui.button(label="📐 Channels", style=discord.ButtonStyle.blurple, row=1)
    async def channels_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="ChannelCog")

    @discord.ui.button(label="🤖 AI", style=discord.ButtonStyle.blurple, row=1)
    async def ai_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="AICog")

    # ------------------------------------------------------------------
    # Row 2 — Platform & Diagnostics + the moderation-side shortcuts.
    # ------------------------------------------------------------------

    @discord.ui.button(label="🛰 Platform", style=discord.ButtonStyle.blurple, row=2)
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

    @discord.ui.button(label="🩺 Diagnostics", style=discord.ButtonStyle.blurple, row=2)
    async def diagnostics_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="DiagnosticCog")

    @discord.ui.button(label="🧪 UX Lab", style=discord.ButtonStyle.blurple, row=2)
    async def uxlab_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="UX Lab")

    @discord.ui.button(label="📝 Logging", style=discord.ButtonStyle.blurple, row=2)
    async def logging_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="LoggingCog")

    @discord.ui.button(label="🧹 Cleanup", style=discord.ButtonStyle.blurple, row=2)
    async def cleanup_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await self._open_via_help_hook(interaction, cog_name="Cleanup")

    # ------------------------------------------------------------------
    # Row 3 — help shortcut
    # ------------------------------------------------------------------

    @discord.ui.button(label="📚 Help", style=discord.ButtonStyle.blurple, row=3)
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
        await safe_edit(
            interaction,
            embed=sub_embed,
            view=sub_view,
            attachments=help_nav_attachments(sub_view),
        )


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
