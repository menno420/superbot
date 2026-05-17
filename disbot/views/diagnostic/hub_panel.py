"""Diagnostics hub view (S4.4.5 extraction).

``_DiagnosticsHubView`` is the ephemeral admin dashboard opened by
``!diagnostics`` (and reachable via the help-menu direct-navigation
hook).  Each button delegates back to the owning ``DiagnosticCog``
text command via ``ctx.invoke`` — this avoids re-implementing each
diagnostic flow inside the view.

The cog reference is held on the view instance (constructor argument)
so the button callbacks have access without a global lookup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer
from views.base import HubView

if TYPE_CHECKING:
    from cogs.diagnostic_cog import DiagnosticCog


class _DiagnosticsHubView(HubView):
    """Interactive hub for all diagnostic tools."""

    def __init__(self, ctx: commands.Context, cog: DiagnosticCog):
        super().__init__(ctx.author)
        self.ctx = ctx
        self.cog = cog

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🔧 Diagnostics Hub",
            description=(
                "Select a diagnostic tool below.\n"
                "All tools require Administrator permission."
            ),
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="🤖 Bot Status",
            value="Health & performance metrics",
            inline=True,
        )
        embed.add_field(name="📡 Latency", value="WebSocket ping", inline=True)
        embed.add_field(
            name="💻 System Info",
            value="OS, disk & Python version",
            inline=True,
        )
        embed.add_field(
            name="🗄️ Check Database",
            value="Verify all DB tables exist",
            inline=True,
        )
        embed.add_field(
            name="📄 Validate JSON",
            value="Check data file integrity",
            inline=True,
        )
        embed.add_field(
            name="📋 Command List",
            value="Paginated command overview",
            inline=True,
        )
        embed.add_field(
            name="🔍 Recent Errors",
            value="Last 10 error log entries",
            inline=True,
        )
        embed.add_field(
            name="🔔 Test Notify",
            value="Fire a test webhook ping",
            inline=True,
        )
        embed.set_footer(text="Diagnostics Hub  •  Admin only")
        return embed

    @discord.ui.button(label="🤖 Bot Status", style=discord.ButtonStyle.blurple, row=0)
    async def btn_status(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.diagnostic_bot_status)

    @discord.ui.button(label="📡 Latency", style=discord.ButtonStyle.blurple, row=0)
    async def btn_latency(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.latency)

    @discord.ui.button(label="💻 System Info", style=discord.ButtonStyle.blurple, row=0)
    async def btn_sysinfo(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.system_info)

    @discord.ui.button(label="🗄️ Database", style=discord.ButtonStyle.grey, row=1)
    async def btn_db(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.check_database)

    @discord.ui.button(label="📄 JSON Files", style=discord.ButtonStyle.grey, row=1)
    async def btn_json(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.validate_json_files)

    @discord.ui.button(label="📋 Commands", style=discord.ButtonStyle.grey, row=1)
    async def btn_cmds(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.list_commands_detailed)

    @discord.ui.button(
        label="🔍 Recent Errors",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def btn_errors(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.recent_errors)

    @discord.ui.button(
        label="🔔 Test Notify",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def btn_notify(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        await self.ctx.invoke(self.cog.test_notification)
