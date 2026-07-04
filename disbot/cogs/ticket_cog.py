"""Support tickets — Discord plumbing only.

A staff support-ticket system. Members open a private ticket channel by
command (``!ticket new``), by clicking the launcher panel, or by asking the
AI in natural language; staff claim, add/remove participants, and close it
(closing posts a transcript + DMs the opener).

The decomposition mirrors treasury/fishing:

    services/ticket_service.py   — read model + open eligibility (read-only)
    services/ticket_mutation.py  — the audited write boundary
    utils/db/tickets.py          — the migration-098 CRUD
    views/tickets/               — launcher / control / hub panels

This file holds only commands, the cog lifecycle, the ``ticket.opened`` UI
listener (the single seam that renders the welcome + control panel for every
open path), and the Help-menu hook.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.events import bus
from core.runtime import guild_resources
from core.runtime.permission_checks import perms_or_owner
from services import ticket_mutation, ticket_service
from views.tickets import (
    TicketConfirmView,
    TicketControlView,
    TicketLauncherView,
    build_confirm_embed,
    build_control_view,
    build_welcome_embed,
    open_ticket_config_panel,
    open_ticket_hub,
    post_launcher,
)

logger = logging.getLogger("bot.cogs.ticket")


class TicketCog(commands.Cog):
    """Command surface + lifecycle for the support-ticket subsystem."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        # Register the persistent panels so their buttons survive restarts
        # (anchor-free + static custom_ids — the SetupLauncherView precedent).
        self.bot.add_view(TicketLauncherView())
        self.bot.add_view(TicketControlView())
        bus.on("ticket.opened", self._on_ticket_opened)
        bus.on("ticket.open_requested", self._on_ticket_open_requested)

    async def cog_check(self, ctx: commands.Context) -> bool:
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    # ------------------------------------------------------------------ events

    async def _on_ticket_opened(
        self,
        *,
        guild_id: int,
        ticket_id: int,
        channel_id: int,
        opener_id: int,
        subject: str,
        source: str,
    ) -> None:
        """Render the welcome embed + control panel inside the new ticket channel.

        The single UI seam for every open path (command / panel / AI). Best
        effort: if this is lost the channel still exists and staff can use the
        ``!ticket`` commands.
        """
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        cfg = await ticket_service.get_config(guild_id)
        content = None
        if cfg is not None and cfg.ping_staff_on_open and cfg.staff_role_id:
            content = f"<@&{cfg.staff_role_id}>"
        embed = build_welcome_embed(ticket_id, f"<@{opener_id}>", subject)
        try:
            await channel.send(content=content, embed=embed, view=build_control_view())
        except Exception:  # pragma: no cover — best-effort UI
            logger.exception(
                "ticket.opened: control panel post failed for %s",
                channel_id,
            )

    async def _on_ticket_open_requested(
        self,
        *,
        guild_id: int,
        channel_id: int,
        user_id: int,
        subject: str,
    ) -> None:
        """Post the one-click confirm panel after the AI proposes a ticket.

        The AI tool ``open_support_ticket`` validated eligibility and emitted
        ``ticket.open_requested``; here we post the [Open ticket]/[Cancel]
        prompt so the user — not the AI — commits the actual open.
        """
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        guild = channel.guild
        member = guild_resources.resolve_member(guild, user_id)
        if member is None:
            return
        try:
            await channel.send(
                content=member.mention,
                embed=build_confirm_embed(subject),
                view=TicketConfirmView(member, subject),
            )
        except Exception:  # pragma: no cover — best-effort UI
            logger.exception(
                "ticket.open_requested: confirm post failed for %s",
                channel_id,
            )

    # ------------------------------------------------------------------ commands

    @commands.group(name="ticket", invoke_without_command=True)
    async def ticket(self, ctx: commands.Context) -> None:
        """Open the ticket hub — open a ticket or view your open tickets."""
        embed, view = await open_ticket_hub(ctx.author, ctx.guild)
        view.message = await ctx.send(embed=embed, view=view)

    @ticket.command(name="new", aliases=["open", "create"])  # type: ignore[arg-type]
    async def ticket_new(self, ctx: commands.Context, *, subject: str = "") -> None:
        """Open a ticket directly: ``!ticket new <subject>``."""
        if not subject.strip():
            await ctx.send("Describe your issue: `!ticket new <subject>`.")
            return
        result = await ticket_mutation.open_ticket(
            ctx.guild,
            ctx.author,
            subject,
            source="command",
        )
        await ctx.send(result.message)

    @ticket.command(name="close")  # type: ignore[arg-type]
    async def ticket_close(self, ctx: commands.Context, *, reason: str = "") -> None:
        """Close the ticket in this channel (staff or the opener)."""
        ticket = await ticket_service.get_ticket_for_channel(ctx.channel.id)
        if ticket is None or ticket.get("status") != "open":
            await ctx.send("This isn't an open ticket channel.")
            return
        cfg = await ticket_service.get_config(ctx.guild.id)
        from views.tickets import is_ticket_staff

        if ctx.author.id != int(ticket["opener_id"]) and not is_ticket_staff(
            ctx.author,
            cfg,
        ):
            await ctx.send("Only staff or the ticket opener can close this ticket.")
            return
        await ctx.send("🔒 Closing this ticket…")
        await ticket_mutation.close_ticket(
            ctx.channel,
            ticket,
            ctx.author,
            reason=reason or None,
        )

    @ticket.command(name="claim")  # type: ignore[arg-type]
    async def ticket_claim(self, ctx: commands.Context) -> None:
        """Claim the ticket in this channel (staff)."""
        ticket = await ticket_service.get_ticket_for_channel(ctx.channel.id)
        if ticket is None or ticket.get("status") != "open":
            await ctx.send("This isn't an open ticket channel.")
            return
        cfg = await ticket_service.get_config(ctx.guild.id)
        from views.tickets import is_ticket_staff

        if not is_ticket_staff(ctx.author, cfg):
            await ctx.send("Only staff can claim tickets.")
            return
        result = await ticket_mutation.claim_ticket(ticket, ctx.author)
        await ctx.send(result.message)

    @ticket.command(name="add")  # type: ignore[arg-type]
    async def ticket_add(self, ctx: commands.Context, member: discord.Member) -> None:
        """Add a member to this ticket (staff)."""
        ticket = await ticket_service.get_ticket_for_channel(ctx.channel.id)
        if ticket is None or ticket.get("status") != "open":
            await ctx.send("This isn't an open ticket channel.")
            return
        cfg = await ticket_service.get_config(ctx.guild.id)
        from views.tickets import is_ticket_staff

        if not is_ticket_staff(ctx.author, cfg):
            await ctx.send("Only staff can add members.")
            return
        result = await ticket_mutation.add_participant(ctx.channel, member, ctx.author)
        await ctx.send(result.message)

    @ticket.command(name="remove")  # type: ignore[arg-type]
    async def ticket_remove(
        self,
        ctx: commands.Context,
        member: discord.Member,
    ) -> None:
        """Remove a member from this ticket (staff)."""
        ticket = await ticket_service.get_ticket_for_channel(ctx.channel.id)
        if ticket is None or ticket.get("status") != "open":
            await ctx.send("This isn't an open ticket channel.")
            return
        cfg = await ticket_service.get_config(ctx.guild.id)
        from views.tickets import is_ticket_staff

        if not is_ticket_staff(ctx.author, cfg):
            await ctx.send("Only staff can remove members.")
            return
        result = await ticket_mutation.remove_participant(
            ctx.channel,
            member,
            ctx.author,
        )
        await ctx.send(result.message)

    # ----- admin / setup --------------------------------------------------- #

    @commands.command(name="ticketpanel")
    @perms_or_owner(manage_guild=True)
    async def ticket_panel(self, ctx: commands.Context) -> None:
        """Post the public ticket launcher panel in this channel (managers)."""
        await post_launcher(ctx.channel)
        await ctx.message.add_reaction("📮")

    @commands.command(name="ticketsetup")
    @perms_or_owner(manage_guild=True)
    async def ticket_setup(
        self,
        ctx: commands.Context,
        staff_role: discord.Role | None = None,
        log_channel: discord.TextChannel | None = None,
    ) -> None:
        """Configure tickets — opens a button/dropdown panel (managers).

        With no arguments, opens the interactive setup panel (pick the staff
        role + log channel from dropdowns, auto-create a log channel, enable,
        and post the panel — no typing). The positional
        ``!ticketsetup @StaffRole [#log-channel]`` form stays for power users.
        """
        if staff_role is None:
            embed, view = await open_ticket_config_panel(ctx.author, guild=ctx.guild)
            await ctx.send(embed=embed, view=view)
            return
        await ticket_mutation.update_config(
            ctx.guild.id,
            ctx.author.id,
            enabled=True,
            staff_role_id=staff_role.id,
            log_channel_id=log_channel.id if log_channel else None,
        )
        extra = f" · log {log_channel.mention}" if log_channel else ""
        await ctx.send(
            f"✅ Tickets enabled — staff role {staff_role.mention}{extra}.\n"
            "Post a panel with `!ticketpanel`, or members can use `!ticket new`.",
        )

    @commands.command(name="ticketlimit")
    @perms_or_owner(manage_guild=True)
    async def ticket_limit(self, ctx: commands.Context, max_open: int) -> None:
        """Set the max simultaneously-open tickets per member (managers)."""
        max_open = max(1, min(max_open, 25))
        await ticket_mutation.update_config(
            ctx.guild.id,
            ctx.author.id,
            max_open_per_user=max_open,
        )
        await ctx.send(f"✅ Members may now hold up to **{max_open}** open ticket(s).")

    @commands.group(name="ticketblacklist", invoke_without_command=True)
    @perms_or_owner(manage_guild=True)
    async def ticket_blacklist(self, ctx: commands.Context) -> None:
        """Manage who may open tickets: ``!ticketblacklist add|remove @user``."""
        await ctx.send("Usage: `!ticketblacklist add|remove @user`.")

    @ticket_blacklist.command(name="add")  # type: ignore[arg-type]
    async def blacklist_add(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "",
    ) -> None:
        result = await ticket_mutation.set_blacklist(
            ctx.guild.id,
            member.id,
            ctx.author.id,
            blacklisted=True,
            reason=reason or None,
        )
        await ctx.send(result.message)

    @ticket_blacklist.command(name="remove")  # type: ignore[arg-type]
    async def blacklist_remove(
        self,
        ctx: commands.Context,
        member: discord.Member,
    ) -> None:
        result = await ticket_mutation.set_blacklist(
            ctx.guild.id,
            member.id,
            ctx.author.id,
            blacklisted=False,
        )
        await ctx.send(result.message)

    # ------------------------------------------------------------------ help hook

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — the ticket hub panel."""
        if interaction.guild is None or not isinstance(
            interaction.user,
            discord.Member,
        ):
            return (
                discord.Embed(description="Tickets are only available in a server."),
                discord.ui.View(),
            )
        return await open_ticket_hub(interaction.user, interaction.guild)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TicketCog(bot))
    logger.info("TicketCog loaded.")
