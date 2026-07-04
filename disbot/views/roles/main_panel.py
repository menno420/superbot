from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime.permission_checks import member_has_perms_or_owner
from utils.ui_constants import ROLE_COLOR
from views.base import BaseView, interaction_is_admin


class RoleHubView(BaseView):
    """Primary role management hub — opened by !roles."""

    def __init__(self, ctx: commands.Context, cog) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.cog = cog

    def build_embed(self) -> discord.Embed:
        return discord.Embed(
            title="🎭 Role Hub",
            description=(
                "**📝 Create** — create a new server role\n"
                "**🗂️ Manage** — view, edit, or delete roles\n"
                "**⏱️ Time Roles** — days-in-server auto-assignment\n"
                "**⚡ XP Roles** — level-based auto-assignment\n"
                "**💬 Reaction Roles** — emoji reaction role bindings\n"
                "**🔧 Diagnostics** — system status & debug tools"
            ),
            color=ROLE_COLOR,
        )

    # ---- Row 0: Create · Manage · Time Roles

    @discord.ui.button(label="📝 Create", style=discord.ButtonStyle.green, row=0)
    async def create_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not member_has_perms_or_owner(interaction.user, manage_roles=True):
            await interaction.response.send_message(
                "❌ You need **Manage Roles** permission.",
                ephemeral=True,
            )
            return
        from views.roles.creation_panel import RoleCreatePanel

        panel = RoleCreatePanel(self.ctx, parent=self)
        panel.message = self.message
        await interaction.response.edit_message(
            embed=panel.build_embed(),
            view=panel,
        )

    @discord.ui.button(label="🗂️ Manage", style=discord.ButtonStyle.blurple, row=0)
    async def manage_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not member_has_perms_or_owner(interaction.user, manage_roles=True):
            await interaction.response.send_message(
                "❌ You need **Manage Roles** permission.",
                ephemeral=True,
            )
            return
        from views.roles.management_panel import ManagementPanel

        panel = ManagementPanel(self.ctx, parent=self)
        panel.message = self.message
        await interaction.response.edit_message(
            embed=await panel.build_embed(),
            view=panel,
        )

    @discord.ui.button(label="⏱️ Time Roles", style=discord.ButtonStyle.blurple, row=0)
    async def time_roles_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need **Administrator** permission.",
                ephemeral=True,
            )
            return
        from views.roles.time_roles_panel import TimeRolesPanel

        panel = TimeRolesPanel(self.ctx, parent=self)
        panel.message = self.message
        await interaction.response.edit_message(
            embed=await panel.build_embed(),
            view=panel,
        )

    # ---- Row 1: XP Roles · Reaction Roles · Diagnostics

    @discord.ui.button(label="⚡ XP Roles", style=discord.ButtonStyle.blurple, row=1)
    async def xp_roles_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need **Administrator** permission.",
                ephemeral=True,
            )
            return
        from views.roles.xp_roles_panel import XpRolesPanel

        panel = XpRolesPanel(self.ctx, parent=self)
        panel.message = self.message
        await interaction.response.edit_message(
            embed=await panel.build_embed(),
            view=panel,
        )

    @discord.ui.button(
        label="💬 Reaction Roles",
        style=discord.ButtonStyle.blurple,
        row=1,
    )
    async def reaction_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.roles.reaction_panel import ReactionRolesPanel

        panel = ReactionRolesPanel(self.ctx, parent=self)
        panel.message = self.message
        await interaction.response.edit_message(
            embed=await panel.build_embed(),
            view=panel,
        )

    @discord.ui.button(label="🔧 Diagnostics", style=discord.ButtonStyle.grey, row=1)
    async def diagnostics_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need **Administrator** permission.",
                ephemeral=True,
            )
            return
        from views.roles.diagnostics_panel import DiagnosticsPanel

        panel = DiagnosticsPanel(self.ctx, parent=self)
        panel.message = self.message
        await interaction.response.edit_message(
            embed=await panel.build_embed(),
            view=panel,
        )
