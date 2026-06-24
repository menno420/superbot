"""Ticket configuration panel — fully button/dropdown driven, no typing.

The single interactive surface for standing tickets up: pick a **staff role**
and **transcript log** from native dropdowns (so a role/channel name can never
be mistyped), one-click **auto-create** the log channel if you don't have one,
**Enable**, and **post the open-ticket panel** — all without a command argument.

Reused by two consumers: the `!setup` wizard's Support Tickets section
(`views/setup/sections/ticket.py`) and the `!ticketsetup` command
(`cogs/ticket_cog.py`). It lives in the ticket domain (`views/tickets/`) rather
than the setup wizard so both can depend on it without the ticket domain
depending on the wizard. All writes go through the audited
`services.ticket_mutation` seam (the direct lane — focused / reversible /
single-domain); ticket config lives in its own table, not the `set_setting`
pipeline, so nothing here stages a draft op.
"""

from __future__ import annotations

import logging

import discord

from core.runtime import guild_resources as resources
from services import ticket_mutation, ticket_service
from views.base import BaseView

logger = logging.getLogger("bot.views.tickets.config_panel")


def build_ticket_config_embed(
    *,
    enabled: bool = False,
    staff_role_id: int | None = None,
    log_channel_id: int | None = None,
    max_open_per_user: int | None = None,
    guild: discord.Guild | None = None,
) -> discord.Embed:
    """Render the config panel, reflecting any pending / current state."""
    embed = discord.Embed(
        title="🎫 Support Tickets",
        description=(
            "Let members open **private support tickets** — a per-member channel "
            "only they and your staff can see. They open one with `!ticket new`, "
            "a button panel, or by asking the AI.\n\n"
            "**1.** Pick a **staff role** below (required).\n"
            "**2.** Pick a **transcript log** channel, or tap **Auto-create** to "
            "make one.\n"
            "**3.** Tap **Enable tickets** — then **Post panel** so members get a "
            "button.\n\n"
            "_Ticket channels are created automatically under a “Tickets” category "
            "when a member opens one — nothing to set up there._"
        ),
        color=discord.Color.blurple(),
    )
    role_text = "_(not set — required)_"
    if staff_role_id:
        role = (
            resources.resolve_role(guild, role_id=staff_role_id)
            if guild is not None
            else None
        )
        role_text = role.mention if role is not None else f"`{staff_role_id}`"
    log_text = "_(none — tap Auto-create or pick one)_"
    if log_channel_id:
        log = guild.get_channel(log_channel_id) if guild is not None else None
        log_text = (
            log.mention
            if isinstance(log, discord.TextChannel)
            else f"`{log_channel_id}`"
        )
    embed.add_field(
        name="Selected" if not enabled else "Current",
        value=(
            f"• Status: **{'enabled' if enabled else 'not enabled yet'}**\n"
            f"• Staff role: {role_text}\n"
            f"• Transcript log: {log_text}\n"
            f"• Max open per user: **{max_open_per_user or 3}**"
        ),
        inline=False,
    )
    embed.set_footer(
        text="Tune limits / blacklist later with !ticketlimit and !ticketblacklist.",
    )
    return embed


class _StaffRoleSelect(discord.ui.RoleSelect):
    """Pick the staff role that can see + manage every ticket."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Staff role (required) — who handles tickets…",
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: TicketConfigPanelView = self.view  # type: ignore[assignment]
        view.staff_role_id = self.values[0].id
        await interaction.response.edit_message(embed=view.render(), view=view)


class _LogChannelSelect(discord.ui.ChannelSelect):
    """Pick the optional channel that closed-ticket transcripts post to."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Transcript log channel (optional)…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: TicketConfigPanelView = self.view  # type: ignore[assignment]
        view.log_channel_id = self.values[0].id
        await interaction.response.edit_message(embed=view.render(), view=view)


class TicketConfigPanelView(BaseView):
    """Dropdowns + Auto-create + Enable + Post-panel — the no-typing setup UI."""

    # A transient config flow, not a navigable hub panel.
    STANDARD_NAV = False

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        guild: discord.Guild | None = None,
        enabled: bool = False,
        staff_role_id: int | None = None,
        log_channel_id: int | None = None,
        max_open_per_user: int | None = None,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self._guild = guild
        self._enabled = enabled
        self.staff_role_id = staff_role_id
        self.log_channel_id = log_channel_id
        self._max_open_per_user = max_open_per_user
        self.add_item(_StaffRoleSelect())
        self.add_item(_LogChannelSelect())

    def render(self) -> discord.Embed:
        return build_ticket_config_embed(
            enabled=self._enabled,
            staff_role_id=self.staff_role_id,
            log_channel_id=self.log_channel_id,
            max_open_per_user=self._max_open_per_user,
            guild=self._guild,
        )

    @discord.ui.button(
        label="Auto-create log channel",
        emoji="🪄",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def autocreate_log(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Tickets can only be configured inside a server.",
                ephemeral=True,
            )
            return
        result = await ticket_mutation.create_log_channel(
            guild,
            interaction.user.id,
            staff_role_id=self.staff_role_id,
        )
        if not result.success:
            await interaction.response.send_message(result.message, ephemeral=True)
            return
        self.log_channel_id = result.channel_id
        await interaction.response.edit_message(embed=self.render(), view=self)
        await interaction.followup.send(result.message, ephemeral=True)

    @discord.ui.button(
        label="Enable tickets",
        emoji="✅",
        style=discord.ButtonStyle.success,
        row=2,
    )
    async def enable(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Tickets can only be configured inside a server.",
                ephemeral=True,
            )
            return
        if self.staff_role_id is None:
            await interaction.response.send_message(
                "Pick a **staff role** first — it's who can see and handle tickets.",
                ephemeral=True,
            )
            return
        await ticket_mutation.update_config(
            guild.id,
            interaction.user.id,
            enabled=True,
            staff_role_id=self.staff_role_id,
            log_channel_id=self.log_channel_id,
        )
        self._enabled = True
        embed = self.render()
        embed.color = discord.Color.green()
        embed.set_footer(
            text="Tickets are live. Tap Post panel so members can open one.",
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Post open-ticket panel here",
        emoji="📋",
        style=discord.ButtonStyle.secondary,
        row=3,
    )
    async def post_panel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        if not self._enabled:
            await interaction.response.send_message(
                "Enable tickets first, then post the panel.",
                ephemeral=True,
            )
            return
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "Run this in a normal text channel to post the panel.",
                ephemeral=True,
            )
            return
        from views.tickets import post_launcher

        try:
            await post_launcher(channel)
        except discord.Forbidden:
            await interaction.response.send_message(
                "I need permission to send messages in this channel.",
                ephemeral=True,
            )
            return
        # Reflect the result in the config panel itself (edit in place).
        embed = self.render()
        embed.color = discord.Color.green()
        embed.set_footer(text=f"📮 Open-ticket panel posted in #{channel.name}.")
        await interaction.response.edit_message(embed=embed, view=self)


async def open_ticket_config_panel(
    interaction_or_ctx_author: discord.Member | discord.User,
    *,
    guild: discord.Guild,
) -> tuple[discord.Embed, TicketConfigPanelView]:
    """Build the embed + view seeded from the guild's current ticket config.

    Returns ``(embed, view)`` for the caller to send (ephemeral from the wizard,
    or as a normal reply from ``!ticketsetup``). Best-effort config read.
    """
    cfg = None
    try:
        cfg = await ticket_service.get_config(guild.id)
    except Exception:  # pragma: no cover — read is informational
        logger.exception("ticket config panel: get_config failed (guild=%d)", guild.id)
    view = TicketConfigPanelView(
        interaction_or_ctx_author,
        guild=guild,
        enabled=bool(cfg and cfg.enabled),
        staff_role_id=cfg.staff_role_id if cfg else None,
        log_channel_id=cfg.log_channel_id if cfg else None,
        max_open_per_user=cfg.max_open_per_user if cfg else None,
    )
    return view.render(), view


__all__ = [
    "TicketConfigPanelView",
    "build_ticket_config_embed",
    "open_ticket_config_panel",
]
