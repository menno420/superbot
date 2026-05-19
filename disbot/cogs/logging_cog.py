"""LoggingCog — owns the ``!logging`` command group and admin panel.

Extracted from :mod:`cogs.admin_cog` in S7d so the logging
subsystem has its own cog identity.  The :func:`build_help_menu_view`
hook routes ``!help → Logging`` directly to
:class:`LoggingPanelView`, and :func:`cog_load` registers the
:class:`LoggingSchema` introduced in S7a.

The runtime logging behavior (event subscription, embed posting,
counters) continues to live in :mod:`services.server_logging`;
this cog is purely the command/panel surface.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from utils.ui_constants import INFO_COLOR, SUCCESS_COLOR


async def build_logging_status_embed(guild: discord.Guild | None) -> discord.Embed:
    """Build the server-logging status embed.

    The single source of truth for the logging status panel.  Used by
    :meth:`LoggingCog.logging_status`,
    :func:`cogs.logging.panel.build_panel_embed`, and the legacy
    :meth:`AdminCog._AdminPanelView.logging_btn` (which now opens the
    LoggingPanelView; the helper remains available for direct use).
    """
    from services import server_logging

    enabled = await server_logging.is_enabled(guild.id) if guild else False
    auto_create = await server_logging.auto_create_enabled(guild.id) if guild else False
    mod_channel = cleanup_channel = None
    if guild:
        mod_channel = await server_logging.resolve_log_channel(guild, "mod")
        cleanup_channel = await server_logging.resolve_log_channel(guild, "cleanup")
    counters = server_logging.counters_snapshot()["counters"]

    embed = discord.Embed(
        title="📝 Server logging — status",
        color=SUCCESS_COLOR if enabled else INFO_COLOR,
    )
    embed.add_field(
        name="Enabled",
        value="✅ on" if enabled else "⚪ off",
        inline=True,
    )
    embed.add_field(
        name="Auto-create channels",
        value="✅ on" if auto_create else "⚪ off",
        inline=True,
    )
    embed.add_field(
        name="Mod channel",
        value=mod_channel.mention if mod_channel else "*(unset)*",
        inline=False,
    )
    cleanup_value = (
        cleanup_channel.mention if cleanup_channel else "*(falls back to mod)*"
    )
    embed.add_field(
        name="Cleanup channel",
        value=cleanup_value,
        inline=False,
    )
    embed.add_field(
        name="Counters (process-local)",
        value="\n".join(f"`{k}` = {v}" for k, v in sorted(counters.items())),
        inline=False,
    )
    return embed


class LoggingCog(commands.Cog):
    """Logging admin command group + panel hook."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        """Register the S7a logging schema."""
        from cogs.logging.schemas import register_schemas

        register_schemas()

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — opens the logging panel."""
        from cogs.logging.panel import LoggingPanelView, build_panel_embed

        view = LoggingPanelView(interaction.user)
        embed = await build_panel_embed(interaction.guild)
        return embed, view

    # ------------------------------------------------------------------
    # !logging — command group
    # ------------------------------------------------------------------

    @commands.group(name="logging", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def logging_grp(self, ctx: commands.Context) -> None:
        """Open the logging admin panel (S7d).

        With a subcommand, dispatches to ``status`` / ``test`` /
        ``set`` / ``create``.  With no subcommand, opens the
        interactive :class:`LoggingPanelView`.
        """
        from cogs.logging.panel import LoggingPanelView, build_panel_embed
        from views.base import send_panel

        view = LoggingPanelView(ctx.author)
        embed = await build_panel_embed(ctx.guild)
        await send_panel(ctx, embed=embed, view=view)

    @logging_grp.command(name="status")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def logging_status(self, ctx: commands.Context) -> None:
        """Show this guild's server-logging configuration + counters."""
        await ctx.send(embed=await build_logging_status_embed(ctx.guild))

    @logging_grp.command(name="set")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def logging_set(self, ctx: commands.Context, kind: str = "") -> None:
        """Open the channel-select view for ``mod`` or ``cleanup`` binding."""
        from cogs.logging.select_view import LogChannelSelectView

        kind = kind.strip().lower()
        if kind not in ("mod", "cleanup"):
            await ctx.send(
                "Usage: `!logging set <mod|cleanup>` — opens the channel "
                "selector for the requested log binding.",
                delete_after=20,
            )
            return
        if ctx.guild is None:
            await ctx.send(
                "`!logging set` requires a guild context.",
                delete_after=15,
            )
            return
        view = LogChannelSelectView(ctx.author, kind)
        await ctx.send(
            (
                f"Pick a channel to bind as the **{kind} log** for this guild.  "
                "All writes route through `BindingMutationPipeline` and "
                "produce an audit row."
            ),
            view=view,
        )

    @logging_grp.command(name="create")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def logging_create(self, ctx: commands.Context, kind: str = "") -> None:
        """Preview + create a new log channel for ``mod`` or ``cleanup``."""
        from cogs.logging.provision_view import (
            LogChannelProvisionView,
            build_preview_embed,
        )

        kind = kind.strip().lower()
        if kind not in ("mod", "cleanup"):
            await ctx.send(
                "Usage: `!logging create <mod|cleanup>` — opens a "
                "preview + Confirm view for the requested channel.",
                delete_after=20,
            )
            return
        if ctx.guild is None:
            await ctx.send(
                "`!logging create` requires a guild context.",
                delete_after=15,
            )
            return
        preview_embed, allowed = await build_preview_embed(ctx.guild, kind)
        view = LogChannelProvisionView(ctx.author, kind, confirm_enabled=allowed)
        await ctx.send(embed=preview_embed, view=view)

    @logging_grp.command(name="test")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def logging_test(self, ctx: commands.Context) -> None:
        """Send a synthetic warn embed to the configured log channel."""
        from services import server_logging

        if ctx.guild is None:
            await ctx.send("This command requires a guild context.")
            return
        sent = await server_logging.log_event(
            ctx.guild,
            action="warn",
            target_id=ctx.author.id,
            actor_id=ctx.author.id,
            reason="server_logging test event from !logging test",
        )
        if sent:
            await ctx.send("✅ Test embed delivered to the configured log channel.")
        else:
            await ctx.send(
                "ℹ️ No embed sent — see `!logging status` for the cause "
                "(disabled / missing channel / send error counted).",
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LoggingCog(bot))
