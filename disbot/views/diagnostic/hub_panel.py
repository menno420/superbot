"""Diagnostics hub view (S4.4.5 + stabilization).

``_DiagnosticsHubView`` is the ephemeral admin dashboard opened by
``!diagnostics`` and (via ``build_help_menu_view``) by the help-menu
"Diagnostics" selection.

Canonical panel pattern: each button uses ``safe_defer`` then
``safe_edit(interaction, embed=..., view=self)`` to update THIS panel
in place — exactly like ``views/economy/main_panel.EconomyPanelView``
and ``views/moderation/main_panel.ModPanelView``.  The hub never
delegates to text commands and never sends new messages from button
callbacks.

Pre-stabilization (S4.4.5 initial extraction) this view delegated to
``self.ctx.invoke(self.cog.<command>)`` which (a) broke under
``help_ctx_shim`` (no ``.invoke``) and (b) produced new messages
instead of editing the panel.  Both issues are resolved by computing
the embed directly via the shared helpers in ``services.diagnostic_helpers``.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services.diagnostic_helpers import (
    build_bot_status_embed,
    build_check_database_embed,
    build_command_list_pages,
    build_hub_overview_embed,
    build_latency_embed,
    build_query_logs_embed,
    build_system_info_embed,
    build_test_notification_embed,
    build_validate_json_embed,
)
from views.base import HubView
from views.diagnostic.paginator import _PaginatorView


class _DiagnosticsHubView(HubView):
    """Interactive hub for all diagnostic tools.

    Constructor takes only the invoking ``author`` — the view reads
    ``bot`` from ``interaction.client`` inside each callback, matching
    the canonical panel pattern.  No ``ctx`` or ``cog`` reference is
    held; the help-menu invocation path (which passes a
    ``help_ctx_shim`` SimpleNamespace) is therefore safe.
    """

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)

    def build_embed(self) -> discord.Embed:
        return build_hub_overview_embed()

    # ------------------------------------------------------------------
    # Row 0 — primary tools
    # ------------------------------------------------------------------

    @discord.ui.button(label="🤖 Bot Status", style=discord.ButtonStyle.blurple, row=0)
    async def btn_status(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        embed = build_bot_status_embed(interaction.client)  # type: ignore[arg-type]
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="📡 Latency", style=discord.ButtonStyle.blurple, row=0)
    async def btn_latency(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        embed = build_latency_embed(interaction.client)  # type: ignore[arg-type]
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="💻 System Info", style=discord.ButtonStyle.blurple, row=0)
    async def btn_sysinfo(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        embed = build_system_info_embed()
        await safe_edit(interaction, embed=embed, view=self)

    # ------------------------------------------------------------------
    # Row 1 — data integrity
    # ------------------------------------------------------------------

    @discord.ui.button(label="🗄️ Database", style=discord.ButtonStyle.grey, row=1)
    async def btn_db(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        embed = await build_check_database_embed()
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="📄 JSON Files", style=discord.ButtonStyle.grey, row=1)
    async def btn_json(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        embed = build_validate_json_embed()
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="📋 Commands", style=discord.ButtonStyle.grey, row=1)
    async def btn_cmds(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Swap the view to a paginator — different control set than the hub.

        The paginator carries a "↩ Back" button so the user can return
        to this hub view in place (canonical sub-panel return pattern).
        """
        if not await safe_defer(interaction):
            return
        pages = build_command_list_pages(interaction.client)  # type: ignore[arg-type]
        if not pages:
            # Edge case: no cogs with commands.  Stay in hub, just show a notice.
            empty = discord.Embed(
                title="Command List",
                description="No cogs with commands found.",
                color=discord.Color.blue(),
            )
            await safe_edit(interaction, embed=empty, view=self)
            return
        paginator = _PaginatorView(pages, self._author, parent_view=self)
        await safe_edit(interaction, embed=pages[0], view=paginator)

    # ------------------------------------------------------------------
    # Row 2 — alerts
    # ------------------------------------------------------------------

    @discord.ui.button(
        label="🔍 Recent Errors",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def btn_errors(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        embed = await build_query_logs_embed(event_type="ERROR", limit=10)
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(
        label="🔔 Test Notify",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def btn_notify(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        embed = await build_test_notification_embed(interaction.client)  # type: ignore[arg-type]
        await safe_edit(interaction, embed=embed, view=self)
