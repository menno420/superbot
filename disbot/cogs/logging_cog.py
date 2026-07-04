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

from core.runtime.permission_checks import admin_or_owner
from utils.ui_constants import INFO_COLOR, SUCCESS_COLOR


async def build_logging_status_embed(guild: discord.Guild | None) -> discord.Embed:
    """Build the server-logging status embed.

    The single source of truth for the logging status panel.  Used by
    :meth:`LoggingCog.logging_status`,
    :func:`cogs.logging.panel.build_panel_embed`, and the legacy
    :meth:`AdminCog._AdminPanelView.logging_btn` (which now opens the
    LoggingPanelView; the helper remains available for direct use).
    """
    from services import server_logging, server_logging_config

    enabled = await server_logging.is_enabled(guild.id) if guild else False
    auto_create = await server_logging.auto_create_enabled(guild.id) if guild else False
    mod_channel = cleanup_channel = events_channel = None
    if guild:
        mod_channel = await server_logging.resolve_log_channel(guild, "mod")
        cleanup_channel = await server_logging.resolve_log_channel(guild, "cleanup")
        events_channel = await server_logging.resolve_log_channel(guild, "events")
    event_policy = (
        await server_logging_config.load_policy(guild.id)
        if guild
        else server_logging_config.EventLoggingPolicy()
    )
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
    # Server event logging (Q-0109 v1 + audit-log v2) — categories + routing.
    active_categories = [
        name
        for name, on in (
            ("messages", event_policy.messages_enabled),
            ("members", event_policy.members_enabled),
            ("roles", event_policy.roles_enabled),
            # v2 (Discord audit-log integration) + voice.
            ("moderation", event_policy.moderation_enabled),
            ("channels", event_policy.channels_enabled),
            ("server", event_policy.server_enabled),
            ("voice", event_policy.voice_enabled),
        )
        if on
    ]
    events_channel_value = events_channel.mention if events_channel else "*(unset)*"
    embed.add_field(
        name="Event logging",
        value=(
            f"Categories: {', '.join(active_categories) if active_categories else '*(none)*'}\n"
            f"Routing: `{event_policy.routing}`\n"
            f"Events channel: {events_channel_value}"
        ),
        inline=False,
    )
    # Audit-log v2 health: the moderation/channels/server categories depend on
    # the bot's View-Audit-Log permission — without it Discord never dispatches
    # on_audit_log_entry_create, so those categories are silently inert. Surface
    # it so an operator who "enabled everything" can see the real cause.
    audit_categories_on = (
        event_policy.moderation_enabled
        or event_policy.channels_enabled
        or event_policy.server_enabled
    )
    if audit_categories_on:
        me = getattr(guild, "me", None) if guild else None
        has_view_audit = bool(
            getattr(getattr(me, "guild_permissions", None), "view_audit_log", False),
        )
        embed.add_field(
            name="Audit-log access",
            value=(
                "✅ bot has **View Audit Log**"
                if has_view_audit
                else (
                    "⚠️ bot is **missing View Audit Log** — the moderation / "
                    "channels / server categories cannot receive events until "
                    "the bot is granted this permission."
                )
            ),
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
    # Server event logging v1 (Q-0109) — passive Discord-event listeners
    # ------------------------------------------------------------------
    #
    # Thin glue: each listener applies a cheap structural filter (skip
    # bots / DMs / no-op edits / non-role updates) so the hot path does no
    # DB work, then delegates to the matching ``server_logging.log_*``
    # handler, which loads the per-guild policy, gates on the master +
    # category flags, resolves the routed channel, and posts the embed.
    # The handlers are fully fail-safe — a logging fault is counted and
    # swallowed, never raised back into the gateway.

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Log a deleted message when the messages category is enabled."""
        if message.guild is None or message.author.bot:
            return
        from services import server_logging

        await server_logging.log_message_delete(message)

    @commands.Cog.listener()
    async def on_message_edit(
        self,
        before: discord.Message,
        after: discord.Message,
    ) -> None:
        """Log a message edit when the messages category is enabled.

        Discord also fires ``message_edit`` when embeds/attachments resolve
        on a link with no text change — skip those so the log stays
        meaningful.
        """
        if after.guild is None or after.author.bot:
            return
        if before.content == after.content:
            return
        from services import server_logging

        await server_logging.log_message_edit(before, after)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Log a member join when the members category is enabled.

        Coexists with the autorole cog's own ``on_member_join`` — discord.py
        dispatches the event to every registered listener independently.
        """
        if member.bot:
            return
        from services import server_logging

        await server_logging.log_member_join(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Log a member departure when the members category is enabled."""
        if member.bot:
            return
        from services import server_logging

        await server_logging.log_member_leave(member)

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ) -> None:
        """Log role grants/revocations when the roles category is enabled.

        ``member_update`` also fires for nickname / timeout / avatar
        changes — compute the role diff and skip when it is empty so only
        genuine role events reach the handler.
        """
        if after.bot:
            return
        before_roles = set(before.roles)
        after_roles = set(after.roles)
        added = [r for r in after.roles if r not in before_roles]
        removed = [r for r in before.roles if r not in after_roles]
        if not added and not removed:
            return
        from services import server_logging

        await server_logging.log_role_change(after, added, removed)

    # ------------------------------------------------------------------
    # Server event logging v2 — Discord audit-log + voice + raw deletes
    # ------------------------------------------------------------------
    #
    # The v2 layer. ``on_audit_log_entry_create`` is a single gateway event
    # that surfaces every administrative action Discord records — by anyone,
    # with the actor named — so the log finally matches what a mature logging
    # bot (Dyno) shows: bans/kicks/timeouts, channel/role/server changes,
    # invites, emojis, webhooks. The handler categorises + gates + posts, fully
    # fail-safe. Requires the bot to hold **View Audit Log**; without it Discord
    # never dispatches this event (surfaced in ``!logging status``).

    @commands.Cog.listener()
    async def on_audit_log_entry_create(
        self,
        entry: discord.AuditLogEntry,
    ) -> None:
        """Log a Discord audit-log entry (bans, channel/role/server changes…)."""
        from services import server_logging

        await server_logging.log_audit_entry(entry)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """Log a voice join/leave/move when the voice category is enabled.

        Skips bots (music/util bots would flood the log) and delegates the
        transition classification + same-channel-noise filter to the handler.
        """
        if member.bot:
            return
        from services import server_logging

        await server_logging.log_voice_state(member, before, after)

    @commands.Cog.listener()
    async def on_raw_message_delete(
        self,
        payload: discord.RawMessageDeleteEvent,
    ) -> None:
        """Log a deletion the cached ``on_message_delete`` path could not see.

        Fires for **every** delete, so it defers to ``on_message_delete`` when
        the message was cached (``payload.cached_message`` present — that path
        logs it with content) and only handles the uncached case itself. This
        closes the v1 gap where deleting an older/post-restart message logged
        nothing at all.
        """
        if payload.guild_id is None or payload.cached_message is not None:
            return
        from services import server_logging

        guild = self.bot.get_guild(payload.guild_id)
        await server_logging.log_uncached_message_delete(
            guild,
            payload.channel_id,
            payload.message_id,
        )

    # ------------------------------------------------------------------
    # !logging — command group
    # ------------------------------------------------------------------

    @commands.group(name="logging", invoke_without_command=True)
    @admin_or_owner()
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
    @admin_or_owner()
    async def logging_status(self, ctx: commands.Context) -> None:
        """Show this guild's server-logging configuration + counters."""
        await ctx.send(embed=await build_logging_status_embed(ctx.guild))

    @logging_grp.command(name="set")  # type: ignore[arg-type]
    @admin_or_owner()
    async def logging_set(self, ctx: commands.Context, kind: str = "") -> None:
        """Open the channel-select view for ``mod`` or ``cleanup`` binding."""
        from cogs.logging.select_view import LogChannelSelectView

        # Phase 9b: accept any of the seven routes (mod / cleanup /
        # debug / info / warning / error / audit). The set is sourced
        # from ``services.server_logging._ROUTE_TO_BINDING`` so adding
        # a new route there propagates automatically.
        from services.server_logging import _ROUTE_TO_BINDING

        kind = kind.strip().lower()
        valid_kinds = sorted(_ROUTE_TO_BINDING.keys())
        if kind not in valid_kinds:
            await ctx.send(
                f"Usage: `!logging set <{'|'.join(valid_kinds)}>` — opens "
                "the channel selector for the requested log binding.",
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
    @admin_or_owner()
    async def logging_create(self, ctx: commands.Context, kind: str = "") -> None:
        """Preview + create a new log channel for any registered route."""
        from cogs.logging.provision_view import (
            LogChannelProvisionView,
            build_preview_embed,
        )
        from services.server_logging import _ROUTE_TO_BINDING

        kind = kind.strip().lower()
        valid_kinds = sorted(_ROUTE_TO_BINDING.keys())
        if kind not in valid_kinds:
            await ctx.send(
                f"Usage: `!logging create <{'|'.join(valid_kinds)}>` — opens "
                "a preview + Confirm view for the requested channel.",
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

    @logging_grp.command(name="routes")  # type: ignore[arg-type]
    @admin_or_owner()
    async def logging_routes(self, ctx: commands.Context) -> None:
        """Open the Phase 9b Routes subpage directly.

        Mirrors the LoggingPanelView Routes button — shows every
        configured route (mod / cleanup / debug / info / warning /
        error / audit), its current binding, and Set / Create
        controls per route.
        """
        from cogs.logging.routes_panel import (
            LoggingRoutesView,
            build_routes_embed,
        )
        from views.base import send_panel

        view = LoggingRoutesView(ctx.author)
        embed = await build_routes_embed(ctx.guild)
        await send_panel(ctx, embed=embed, view=view)

    @logging_grp.command(name="test")  # type: ignore[arg-type]
    @admin_or_owner()
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
