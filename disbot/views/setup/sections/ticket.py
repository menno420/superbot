"""Support-tickets section — enable + configure tickets inside the wizard.

Tickets were reachable only via ``!help`` → Community hub or the standalone
``!ticketsetup`` command — invisible to a new owner running the ``!setup``
wizard (the surface they actually start from). This section closes that
discoverability gap: tickets now appear as a wizard step / ``/setup-hub`` button.

Tickets keep their config in a dedicated table (``services.ticket_service`` /
``ticket_mutation``), **not** the generic ``set_setting`` pipeline, so this
section writes through the audited ``ticket_mutation.update_config`` directly —
the same path ``!ticketsetup`` uses. That is the focused / reversible /
single-domain **direct lane** (``docs/ownership.md`` § "Direct vs. draft
mutation lanes"); it stages no ``SetupOperation`` draft rows (``op_kinds`` is
empty), mirroring the ``suggestions`` / ``server_scan`` sections that open their
own panel rather than feeding Final Review.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from core.runtime import guild_resources as resources
from services import setup_session, ticket_mutation, ticket_service
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.ticket")

SLUG = "ticket"


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def build_ticket_setup_embed(
    *,
    enabled: bool = False,
    staff_role_id: int | None = None,
    log_channel_id: int | None = None,
    max_open_per_user: int | None = None,
    guild: discord.Guild | None = None,
) -> discord.Embed:
    """Render the ticket section panel, reflecting any pending / current state."""
    embed = discord.Embed(
        title="🎫 Support Tickets",
        description=(
            "Let members open **private support tickets** — a per-member channel "
            "only they and your staff can see. They can open one with `!ticket "
            "new`, a button panel (`!ticketpanel`), or just by asking the AI.\n\n"
            "Pick a **staff role** (required) and an optional **transcript log "
            "channel**, then **Enable tickets**."
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
    log_text = "_(none — transcripts won't be archived)_"
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


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------


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
        view: TicketSetupSectionView = self.view  # type: ignore[assignment]
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
        view: TicketSetupSectionView = self.view  # type: ignore[assignment]
        view.log_channel_id = self.values[0].id
        await interaction.response.edit_message(embed=view.render(), view=view)


class TicketSetupSectionView(BaseView):
    """Direct-lane ticket config: staff role + log channel + Enable."""

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
        return build_ticket_setup_embed(
            enabled=self._enabled,
            staff_role_id=self.staff_role_id,
            log_channel_id=self.log_channel_id,
            max_open_per_user=self._max_open_per_user,
            guild=self._guild,
        )

    @discord.ui.button(
        label="Enable tickets",
        emoji="🎫",
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
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        embed = self.render()
        embed.color = discord.Color.green()
        embed.set_footer(
            text="Tickets are live. Post a button panel with !ticketpanel.",
        )
        await interaction.response.edit_message(embed=embed, view=self)
        try:
            await setup_session.mark_in_progress(guild.id, step=SLUG)
        except Exception:  # pragma: no cover — progress marker is best-effort
            logger.exception("ticket section: mark_in_progress failed")


# ---------------------------------------------------------------------------
# Section entry points
# ---------------------------------------------------------------------------


async def _open_panel(
    interaction: discord.Interaction,
    hub: SetupHubView | None,
) -> None:
    """Open the ticket config panel (both the hub button + wizard Customize)."""
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This can only be used in a server.",
            ephemeral=True,
        )
        return
    cfg = None
    try:
        cfg = await ticket_service.get_config(guild.id)
    except Exception:  # pragma: no cover — read is informational
        logger.exception("ticket section: get_config failed")
    view = TicketSetupSectionView(
        interaction.user,
        guild=guild,
        enabled=bool(cfg and cfg.enabled),
        staff_role_id=cfg.staff_role_id if cfg else None,
        log_channel_id=cfg.log_channel_id if cfg else None,
        max_open_per_user=cfg.max_open_per_user if cfg else None,
    )
    await interaction.response.send_message(
        embed=view.render(),
        view=view,
        ephemeral=True,
    )


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    """Section entry — open the ticket config panel."""
    await _open_panel(interaction, hub)


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Support Tickets",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="🎫",
        order=72,
        op_kinds=frozenset(),
        description_if_skipped=(
            "Tickets stay disabled — members can't open private support tickets "
            "until you enable them here or run `!ticketsetup @StaffRole [#log]`."
        ),
        depths=frozenset({"standard", "advanced"}),
        customize=_open_panel,
    ),
)


__all__ = [
    "SLUG",
    "TicketSetupSectionView",
    "build_ticket_setup_embed",
    "run",
]
