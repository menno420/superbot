"""LoggingPanelView — S7d admin panel for server-logging customization.

Interactive hub for the logging subsystem.  Buttons open the
existing S7b / S7c flows as ephemeral followups:

* 📝 **Refresh Status** — re-renders the status embed in place.
* 🔗 **Set Mod Channel** — opens :class:`LogChannelSelectView` for
  ``logging.mod_channel`` (ephemeral followup; routes through
  :class:`BindingMutationPipeline`).
* 🔗 **Set Cleanup Channel** — same for ``logging.cleanup_channel``.
* 🆕 **Create Mod Channel** — opens preview + Confirm via
  :class:`LogChannelProvisionView` (ephemeral followup; routes
  through :class:`ResourceProvisioningPipeline`).
* 🆕 **Create Cleanup Channel** — same for cleanup.
* 🔔 **Test** — fires a synthetic warn event via
  :func:`services.server_logging.log_event` (same as
  ``!logging test``).
* ↩ **Overview** — re-renders the status embed (same as Refresh).

The panel is intentionally a thin entry point: every action goes
through an existing audited pipeline.  No mutation happens in this
file; nothing here writes scalar settings, bindings, or resources
directly.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from views.base import HubView

logger = logging.getLogger("bot.cogs.logging.panel")


async def build_panel_embed(guild: discord.Guild | None) -> discord.Embed:
    """Reuse :func:`build_logging_status_embed` as the panel landing embed.

    The panel always opens to the status view so the operator sees
    the current configuration without an extra click.
    """
    from cogs.logging_cog import build_logging_status_embed

    return await build_logging_status_embed(guild)


class LoggingPanelView(HubView):
    """Logging admin hub — Status + Set + Create + Test."""

    SUBSYSTEM = "logging"

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)

    @discord.ui.button(
        label="📝 Refresh Status",
        style=discord.ButtonStyle.blurple,
        row=0,
        custom_id="logging_panel.status",
    )
    async def status_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        embed = await build_panel_embed(interaction.guild)
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="🔗 Set Mod Channel",
        style=discord.ButtonStyle.blurple,
        row=1,
        custom_id="logging_panel.set_mod",
    )
    async def set_mod_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await _open_select(interaction, kind="mod")

    @discord.ui.button(
        label="🔗 Set Cleanup Channel",
        style=discord.ButtonStyle.blurple,
        row=1,
        custom_id="logging_panel.set_cleanup",
    )
    async def set_cleanup_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await _open_select(interaction, kind="cleanup")

    @discord.ui.button(
        label="🆕 Create Mod Channel",
        style=discord.ButtonStyle.success,
        row=2,
        custom_id="logging_panel.create_mod",
    )
    async def create_mod_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await _open_provision(interaction, kind="mod")

    @discord.ui.button(
        label="🆕 Create Cleanup Channel",
        style=discord.ButtonStyle.success,
        row=2,
        custom_id="logging_panel.create_cleanup",
    )
    async def create_cleanup_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await _open_provision(interaction, kind="cleanup")

    @discord.ui.button(
        label="🔔 Test",
        style=discord.ButtonStyle.secondary,
        row=3,
        custom_id="logging_panel.test",
    )
    async def fire_test_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "Test requires a guild context.",
                ephemeral=True,
            )
            return
        if not await safe_defer(interaction, ephemeral=True):
            return
        from services import server_logging

        sent = await server_logging.log_event(
            interaction.guild,
            action="warn",
            target_id=interaction.user.id,
            actor_id=interaction.user.id,
            reason="server_logging test event from LoggingPanelView",
        )
        if sent:
            msg = "✅ Test embed delivered to the configured log channel."
        else:
            msg = (
                "ℹ️ No embed sent — refresh status for the cause "
                "(disabled / missing channel / send error counted)."
            )
        await interaction.followup.send(msg, ephemeral=True)

    @discord.ui.button(
        label="🗺️ Routes",
        style=discord.ButtonStyle.blurple,
        row=3,
        custom_id="logging_panel.routes",
    )
    async def routes_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        """Open the Phase 9b Routes subpage for severity/audit channels."""
        # Local import — routes_panel pulls in server_logging's route
        # tables and the resolver, which we don't need at panel-load
        # time.
        from cogs.logging.routes_panel import (
            LoggingRoutesView,
            build_routes_embed,
        )
        from views.navigation import carry_back

        if not await safe_defer(interaction):
            return
        view = LoggingRoutesView(interaction.user)
        # Carry any externally-attached back (↩ Back to Settings / Help, added
        # by the opener) onto the fresh Routes view so it survives the round
        # trip — without this the panel loses its parent-nav going into Routes.
        carry_back(self, view)
        embed = await build_routes_embed(interaction.guild)
        await safe_edit(interaction, embed=embed, view=view)

    @discord.ui.button(
        label="↩ Overview",
        style=discord.ButtonStyle.secondary,
        row=4,
        custom_id="logging_panel.overview",
    )
    async def overview_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        embed = await build_panel_embed(interaction.guild)
        await safe_edit(interaction, embed=embed, view=self)


# ---------------------------------------------------------------------------
# Sub-action openers — each opens an ephemeral followup
# ---------------------------------------------------------------------------


async def _open_select(interaction: discord.Interaction, *, kind: str) -> None:
    """Open the existing :class:`LogChannelSelectView` as an ephemeral followup."""
    if interaction.guild is None:
        await interaction.response.send_message(
            "This action requires a guild context.",
            ephemeral=True,
        )
        return
    from cogs.logging.select_view import LogChannelSelectView

    view = LogChannelSelectView(interaction.user, kind)
    label = "moderation log" if kind == "mod" else "cleanup log"
    await interaction.response.send_message(
        f"Pick the **{label}** channel.  Writes through "
        "`BindingMutationPipeline` and records an audit row.",
        view=view,
        ephemeral=True,
    )


async def _open_provision(interaction: discord.Interaction, *, kind: str) -> None:
    """Open the existing :class:`LogChannelProvisionView` (with preview)."""
    if interaction.guild is None:
        await interaction.response.send_message(
            "This action requires a guild context.",
            ephemeral=True,
        )
        return
    from cogs.logging.provision_view import (
        LogChannelProvisionView,
        build_preview_embed,
    )

    embed, allowed = await build_preview_embed(interaction.guild, kind)
    view = LogChannelProvisionView(interaction.user, kind, confirm_enabled=allowed)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


__all__ = ["LoggingPanelView", "build_panel_embed"]
