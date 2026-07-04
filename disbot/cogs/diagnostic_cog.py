from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.diagnostic._helpers import (
    build_bot_status_embed,
    build_check_database_embed,
    build_command_list_pages,
    build_latency_embed,
    build_query_logs_embed,
    build_system_info_embed,
    build_test_notification_embed,
    build_validate_json_embed,
)

# ``build_lifecycle_embed`` stays here for the ``!lifecycle`` shortcut command;
# every other ``_platform_embeds`` builder is used by the ``!platform`` group,
# which now lives on ``PlatformCommandsMixin`` (``cogs/diagnostic/platform_group.py``).
from cogs.diagnostic._platform_embeds import build_lifecycle_embed
from cogs.diagnostic.platform_group import PlatformCommandsMixin
from core.runtime.permission_checks import admin_or_owner, app_admin_or_owner
from views.base import send_panel
from views.diagnostic import (
    _DiagnosticsHubView,
    _PaginatorView,
    _PlatformHubView,
    build_platform_hub_embed,
)

logger = logging.getLogger("bot")


class DiagnosticCog(PlatformCommandsMixin, commands.Cog):
    """Advanced diagnostics and monitoring tools.

    The ``!platform`` runtime-introspection group lives on
    :class:`~cogs.diagnostic.platform_group.PlatformCommandsMixin` (its weight
    would otherwise push this file past the 800-LOC cog ceiling); discord.py's
    ``CogMeta`` collects those commands across the MRO, so the group registers
    under this one cog exactly as if it were defined inline.
    """

    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # Diagnostics hub
    # ------------------------------------------------------------------

    @commands.cooldown(rate=2, per=15, type=commands.BucketType.user)
    @commands.command(name="diagnostics", aliases=["diag"])
    @admin_or_owner()
    async def diagnostics_hub(self, ctx):
        """Open the interactive diagnostics hub panel."""
        view = _DiagnosticsHubView(ctx.author)
        await send_panel(ctx, embed=view.build_embed(), view=view)

    @commands.command(name="lifecycle", aliases=["lc"])
    @admin_or_owner()
    async def lifecycle_shortcut(self, ctx):
        """Lifecycle state (phase, pending request, recent events).

        Shortcut for ``!platform lifecycle`` — operators don't need to
        remember the ``platform`` prefix during an incident.  Mirrors
        the existing ``!diag`` → ``!diagnostics`` shortcut pattern.
        """
        await ctx.send(embed=build_lifecycle_embed())

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the diagnostics hub).

        The view reads ``bot`` from ``interaction.client`` inside each
        button callback, so no ctx-shim is required.  This matches the
        canonical pattern used by every other subsystem hub.

        This hook stays pointed at the Diagnostics Hub so the Server &
        Admin panel's Diagnostics button and ``!help diagnostic[s]`` /
        ``!help diag`` open the diagnostics surface. The Platform view is
        a sibling hook, :meth:`build_platform_help_menu_view`, reached via
        the Server & Admin panel's Platform button (help-menu regrouping,
        PR #1290 — Diagnostics/Platform is no longer a top-level hub).
        """
        view = _DiagnosticsHubView(interaction.user)
        return view.build_embed(), view

    async def build_platform_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook for the Platform hub.

        Reached via the Server & Admin panel's Platform button (and the
        ``!platform`` slash/group command). ``DiagnosticCog`` owns both
        surfaces; this sibling hook keeps :meth:`build_help_menu_view`
        free for the Diagnostics callers that already depend on it.

        Reads only ``interaction.user`` — the ``HelpOpener`` adapter is
        a safe drop-in here.
        """
        view = _PlatformHubView(interaction.user)
        return build_platform_hub_embed(), view

    @app_commands.command(
        name="platform",
        description="Open the Platform / Diagnostics hub (administrator only).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    async def platform_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door for the Platform hub — ephemeral, admin-only.

        PR E2 — privileged slash. Mirrors ``!platform`` (gated by
        ``administrator=True``). Reuses
        :meth:`build_platform_help_menu_view` so the slash entry
        opens the same Platform hub as Help → Platform/Diagnostics.
        """
        embed, view = await self.build_platform_help_menu_view(interaction)
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # Command overview
    # ------------------------------------------------------------------

    @commands.command(name="list_commands_detailed", aliases=["listcmds"])
    @admin_or_owner()
    async def list_commands_detailed(self, ctx):
        """List all registered commands with details, paginated by cog."""
        pages = build_command_list_pages(self.bot)
        if not pages:
            await ctx.send("No cogs with commands found.", delete_after=10)
            return
        view = _PaginatorView(pages, ctx.author)
        view.message = await ctx.send(embed=pages[0], view=view)

    @commands.command(name="find_command", aliases=["findcmd"])
    @admin_or_owner()
    async def find_command_cmd(self, ctx, keyword: str):
        """Search for commands by keyword in their name or description."""
        embed = discord.Embed(
            title=f"Search Results for '{keyword}'",
            color=discord.Color.green(),
        )
        found = False
        for cog_name, cog_obj in self.bot.cogs.items():
            for cmd in cog_obj.get_commands():
                if keyword.lower() in cmd.name.lower() or (
                    cmd.help and keyword.lower() in cmd.help.lower()
                ):
                    found = True
                    cd_text = "No cooldown"
                    if cmd._buckets._cooldown:
                        cd = cmd._buckets._cooldown
                        cd_text = f"{cd.rate} use(s) per {cd.per}s"
                    embed.add_field(
                        name=f"!{cmd.name} ({cog_name})",
                        value=(
                            f"{cmd.help or 'No description'}\n"
                            f"Cooldown: {cd_text} | Aliases: {', '.join(cmd.aliases) or 'None'}"
                        ),
                        inline=False,
                    )
        if not found:
            embed.description = "No commands found matching the keyword."
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Data integrity
    # ------------------------------------------------------------------

    @commands.command(name="validate_json_files", aliases=["validatejson"])
    @admin_or_owner()
    async def validate_json_files(self, ctx):
        """Validate the structure of all JSON files in the data directory."""
        embed = build_validate_json_embed()
        await ctx.send(embed=embed)

    @commands.command(name="check_database", aliases=["checkdb"])
    @admin_or_owner()
    async def check_database(self, ctx):
        """Verify that all expected PostgreSQL tables exist."""
        embed = await build_check_database_embed()
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Health & performance
    # ------------------------------------------------------------------

    @commands.command(name="diagnostic_bot_status", aliases=["diag_status"])
    @admin_or_owner()
    async def diagnostic_bot_status(self, ctx):
        """Display bot health and performance metrics."""
        embed = build_bot_status_embed(self.bot)
        await ctx.send(embed=embed)

    @commands.command(name="latency")
    @admin_or_owner()
    async def latency(self, ctx):
        """Report the bot's WebSocket latency (admin detail view).

        The user-facing ``!ping`` lives in the utility cog (user tier); this is
        the admin-tier readout. The ``ping`` alias was re-homed to utility so
        ordinary members have a ping (registry capability ``utility.tool.ping``).
        """
        embed = build_latency_embed(self.bot)
        await ctx.send(embed=embed)

    @commands.command(name="system_info", aliases=["sysinfo"])
    @admin_or_owner()
    async def system_info(self, ctx):
        """Display system-level stats."""
        embed = build_system_info_embed()
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Log queries (PostgreSQL logs table)
    # ------------------------------------------------------------------

    @commands.command(name="query_logs", aliases=["querylogs"])
    @admin_or_owner()
    async def query_logs(self, ctx, event_type: str = None, limit: int = 10):
        """Query recent logs from the logs table.  !query_logs [INFO|ERROR|...] [limit]"""
        embed = await build_query_logs_embed(event_type=event_type, limit=limit)
        await ctx.send(embed=embed)

    @commands.command(name="recent_errors", aliases=["errors"])
    @admin_or_owner()
    async def recent_errors(self, ctx, limit: int = 10):
        """Retrieve the most recent ERROR-level log entries."""
        embed = await build_query_logs_embed(event_type="ERROR", limit=limit)
        await ctx.send(embed=embed)

    @commands.command(name="test_notification", aliases=["testnotify"])
    @admin_or_owner()
    async def test_notification(self, ctx):
        """Send a test notification via the webhook reporter."""
        embed = await build_test_notification_embed(self.bot)
        await ctx.send(embed=embed)


async def setup(bot):
    from cogs.diagnostic._log_buffer import install as install_log_buffer
    from cogs.diagnostic._log_buffer import recent as recent_logs
    from services import diagnostics_service

    install_log_buffer()
    # Expose the in-memory error ring buffer to the services layer (the health
    # read-model must not import cogs) via the diagnostics registry — cogs
    # register *into* it. Bounded; the health aggregator normalizes + groups
    # these before display (PR4, opt-in via HEALTH_GROUPED_FINDINGS).
    diagnostics_service.register(
        "recent_errors",
        lambda: {"recent": recent_logs(level="ERROR", limit=50)},
    )
    await bot.add_cog(DiagnosticCog(bot))
    logger.info("DiagnosticCog loaded.")
